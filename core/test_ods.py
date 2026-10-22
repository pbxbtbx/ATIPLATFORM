import io
import zipfile
from datetime import timedelta
from xml.sax.saxutils import escape
from django.test import TestCase,Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Profile,AcademicYear,ClassGroup,Student,Enrollment,Guardian,GuardianLink,ImportDraft,Consent,Audit
from core.ods_importing import parse_ods,MAX_ROWS

HEADERS=['Nombre Alumno','Apellido Alumno','Date Nacimiento','Form Grupo','Nombre Resp1','Apellido Resp1','Email Resp1','Tel Resp 1','Checkbox Privacidad','Octubre','Observaciones']


def ods(sheets=None):
    sheets=sheets or [('Academia ficticia',HEADERS,[['Persona','Ficticia Uno','2018-01-02','Grupo A','Contacto','Ficticio','familia@example.invalid','600000001','SI','75','NO_IMPORTAR_NOTA'],['Persona','Ficticia Dos','2019-02-03','Grupo B','Contacto','Ficticio','familia@example.invalid','600 000 001','SI','75','NO_IMPORTAR_NOTA']]),('Evento ficticio',HEADERS,[['Persona','Ficticia Evento','2019-01-01','Evento','Contacto','Evento','evento@example.invalid','600000002','','','']])]
    xml='<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"><office:body><office:spreadsheet>'
    for label,headers,rows in sheets:
        xml+='<table:table table:name="'+escape(label,{'"':'&quot;'})+'">'
        for row in [headers]+rows:
            xml+='<table:table-row>'+''.join('<table:table-cell office:value-type="string"><text:p>'+escape(v)+'</text:p></table:table-cell>' for v in row)+'</table:table-row>'
        # Calc rellena filas/columnas en bloques: no deben expandirse.
        xml+='<table:table-row table:number-rows-repeated="1000000"><table:table-cell table:number-columns-repeated="16384"/></table:table-row></table:table>'
    xml+='</office:spreadsheet></office:body></office:document-content>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/vnd.oasis.opendocument.spreadsheet');z.writestr('content.xml',xml)
    return out.getvalue()


class ODSTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('ods.admin');Profile.objects.create(user=self.user,role='admin')
        self.other=User.objects.create_user('ods.other');Profile.objects.create(user=self.other,role='admin')
        self.teacher=User.objects.create_user('ods.teacher');Profile.objects.create(user=self.teacher)
        self.today=timezone.localdate()
        year=AcademicYear.objects.create(name='Curso ficticio',starts=self.today-timedelta(days=30),ends=self.today+timedelta(days=300))
        self.a=ClassGroup.objects.create(name='Destino A',kind='initial',year=year,starts=year.starts,ends=year.ends,capacity=10)
        self.b=ClassGroup.objects.create(name='Destino B',kind='intermediate',year=year,starts=year.starts,ends=year.ends,capacity=10)
        self.client.force_login(self.user)
    def upload(self,data=None):
        response=self.client.post('/imports/',{'kind':'ods','file':SimpleUploadedFile('ficticio.ods',data or ods())})
        self.assertEqual(response.status_code,302)
        return response.url+'ods/'
    def data(self):
        draft=ImportDraft.objects.latest('created_at')
        data={'action':'review','sheets':['0'],'rows':[r['id'] for r in draft.payload['rows']],'joined':self.today.isoformat(),'reuse_contacts':'on','group_0':str(self.a.pk),'group_1':str(self.b.pk)}
        for row in draft.payload['rows']:
            rid=row['id'];data['birth_'+rid]=row['birth'];data['name_'+rid]=row['name']
            for n,contact in enumerate(row['contacts']):
                prefix=f'contact_{rid}_{n}_';data[prefix+'include']='on'
                for field,value in contact.items():data[prefix+field]=value
        return data
    def test_parse_columns_and_no_sensitive_extras(self):
        payload=parse_ods(ods());self.assertEqual(len(payload['rows']),3)
        self.assertNotIn('NO_IMPORTAR_NOTA',str(payload));self.assertNotIn('Privacidad',str(payload));self.assertNotIn('Octubre',str(payload))
        self.assertEqual(set(payload['rows'][0]),{'id','sheet','row','name','birth','group','contacts'})
    def test_multi_group_shared_guardian_preview_and_atomic_confirm(self):
        url=self.upload();self.assertFalse(Student.objects.exists())
        self.assertEqual(self.client.get(url).status_code,200)
        preview=self.client.post(url,self.data());self.assertContains(preview,'Confirmar e importar alumnado y responsables')
        self.assertFalse(Student.objects.exists());self.assertFalse(Guardian.objects.exists())
        self.client.post(url,{'action':'confirm'});self.client.post(url,{'action':'confirm'})
        self.assertEqual(Student.objects.count(),2);self.assertEqual(Guardian.objects.count(),1);self.assertEqual(GuardianLink.objects.count(),2)
        self.assertEqual(Enrollment.objects.filter(group=self.a).count(),1);self.assertEqual(Enrollment.objects.filter(group=self.b).count(),1)
        self.assertEqual(GuardianLink.objects.filter(legal=True).count(),0);self.assertEqual(GuardianLink.objects.filter(priority=True).count(),0)
        self.assertEqual(GuardianLink.objects.filter(emergency=True).count(),0);self.assertEqual(Consent.objects.count(),0)
        self.assertEqual(ImportDraft.objects.get().payload,{})
        self.assertNotIn('familia@example.invalid',str(list(Audit.objects.values())))
    def test_select_only_one_group_and_exclude_invalid_other_sheet(self):
        url=self.upload();data=self.data();data['group_1']='';data['contact_2_0_email']='BAD EMAIL';data['birth_2']='NOT A DATE'
        self.assertContains(self.client.post(url,data),'Confirmar e importar alumnado y responsables')
        self.client.post(url,{'action':'confirm'});self.assertEqual(Student.objects.count(),1);self.assertEqual(Guardian.objects.count(),1)
    def test_no_sheet_or_group_no_review_and_no_confirm_without_review(self):
        url=self.upload();data=self.data();data['sheets']=[]
        self.assertNotContains(self.client.post(url,data),'value="confirm"')
        self.client.post(url,{'action':'confirm'});self.assertFalse(Student.objects.exists())
        data=self.data();data['group_0']='';data['group_1']=''
        self.assertNotContains(self.client.post(url,data),'value="confirm"')
    def test_capacity_revalidated_and_no_partial_family_records(self):
        url=self.upload();data=self.data();self.client.post(url,data)
        self.b.capacity=1;self.b.save();existing=Student.objects.create(name='Ocupante ficticio',joined=self.today);Enrollment.objects.create(student=existing,group=self.b,starts=self.today)
        self.assertContains(self.client.post(url,{'action':'confirm'}),'No hay plazas')
        self.assertEqual(Student.objects.count(),1);self.assertFalse(Guardian.objects.exists())
    def test_repeated_student_requires_confirmation_and_preserves_existing(self):
        rows=[['Persona','Ficticia Uno','2018-01-02','Grupo A','Contacto','Ficticio','familia@example.invalid','600000001','','',''],['Persona','Ficticia Uno','2018-01-02','Grupo B','Contacto','Ficticio','familia@example.invalid','600000001','','','']]
        url=self.upload(ods([('Academia ficticia',HEADERS,rows)]));data=self.data()
        self.assertContains(self.client.post(url,data),'alumnos repetidos')
        data['merge_students']='on';self.assertContains(self.client.post(url,data),'value="confirm"');self.client.post(url,{'action':'confirm'})
        self.assertEqual(Student.objects.count(),1);self.assertEqual(Enrollment.objects.count(),2)
        student=Student.objects.get();student.interests='CONSERVAR_INTERESES';student.save()
        url=self.upload(ods([('Academia ficticia',HEADERS,rows)]));data=self.data();data['merge_students']='on'
        self.assertContains(self.client.post(url,data),'Ya existe un alumno')
        data.update(student_0=str(student.pk),student_1=str(student.pk))
        self.assertContains(self.client.post(url,data),'value="confirm"');self.client.post(url,{'action':'confirm'})
        student.refresh_from_db();self.assertEqual(student.interests,'CONSERVAR_INTERESES');self.assertEqual(Enrollment.objects.count(),2);self.assertEqual(GuardianLink.objects.count(),1)
    def test_contacts_correctable_and_legal_explicit_and_reuse_required(self):
        url=self.upload();data=self.data();data['reuse_contacts']=''
        self.assertContains(self.client.post(url,data),'responsables repetidos')
        data['reuse_contacts']='on';data['contact_0_0_email']='bad-email'
        self.assertNotContains(self.client.post(url,data),'value="confirm"')
        data['contact_0_0_email']='familia@example.invalid';data['legal']='on'
        self.assertContains(self.client.post(url,data),'value="confirm"');self.client.post(url,{'action':'confirm'})
        self.assertEqual(GuardianLink.objects.filter(legal=True).count(),2)
    def test_owner_permissions_csrf_and_expiry(self):
        url=self.upload();self.client.force_login(self.other);self.assertEqual(self.client.get(url).status_code,404)
        self.client.force_login(self.teacher);self.assertEqual(self.client.get(url).status_code,403)
        self.client.force_login(self.user)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user);self.assertEqual(csrf.post(url,self.data()).status_code,403)
        ImportDraft.objects.update(created_at=timezone.now()-timedelta(days=2));self.assertEqual(self.client.get(url).status_code,302)
    def test_fingerprint_rejects_unexpected_reuse_after_preview(self):
        url=self.upload();self.client.post(url,self.data())
        Guardian.objects.create(name='Contacto Ficticio',email='familia@example.invalid',phone='600000001')
        self.assertContains(self.client.post(url,{'action':'confirm'}),'Los datos han cambiado')
        self.assertFalse(Student.objects.exists());self.assertEqual(Guardian.objects.count(),1)
    def test_security_invalid_zip_dtd_and_limits(self):
        for data in (b'bad zip',b''):
            with self.assertRaises(ValidationError):parse_ods(data)
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('mimetype','application/vnd.oasis.opendocument.spreadsheet');z.writestr('content.xml','<!DOCTYPE bad><root/>')
        with self.assertRaises(ValidationError):parse_ods(out.getvalue())
        rows=[['A','Ficticio','','Grupo A','','','','','','',''] for _ in range(MAX_ROWS+1)]
        with self.assertRaises(ValidationError):parse_ods(ods([('Ficticia',HEADERS,rows)]))
        with zipfile.ZipFile(io.BytesIO(ods())) as z:xml=z.read('content.xml').decode()
        for altered in (xml.replace('Nombre Alumno','x'*2001,1),xml.replace('Nombre Alumno','<text:s text:c="2000"/><text:s text:c="2000"/>',1),xml.replace('Nombre Alumno','<text:span>'*45+'Nombre Alumno'+'</text:span>'*45,1)):
            oversized=io.BytesIO()
            with zipfile.ZipFile(oversized,'w') as z:
                z.writestr('mimetype','application/vnd.oasis.opendocument.spreadsheet');z.writestr('content.xml',altered)
            with self.assertRaises(ValidationError):parse_ods(oversized.getvalue())

    def test_missing_contact_name_review_or_exclude_without_losing_student(self):
        url=self.upload();data=self.data();data['contact_0_0_name']=''
        response=self.client.post(url,data)
        self.assertIn('contact_0_0_name',response.context['form'].errors)
        self.assertNotContains(response,'value="confirm"')
        data['contact_0_0_include']='';data['contact_0_0_email']='BAD EMAIL NOT IMPORTED'
        preview=self.client.post(url,data);self.assertContains(preview,'value="confirm"')
        self.assertEqual(preview.context['plan']['excluded_contacts'],1)
        self.client.post(url,{'action':'confirm'});self.assertEqual(Student.objects.count(),2);self.assertEqual(Guardian.objects.count(),1)

    def test_same_name_different_contacts_requires_explicit_separation(self):
        url=self.upload();data=self.data();data['contact_1_0_phone']='600000099';data['contact_1_0_email']='otra-familia@example.invalid'
        response=self.client.post(url,data)
        self.assertIn('contact_1_0_distinct',response.context['form'].errors)
        data['contact_1_0_distinct']='on'
        self.assertContains(self.client.post(url,data),'value="confirm"');self.client.post(url,{'action':'confirm'})
        self.assertEqual(Guardian.objects.count(),2);self.assertEqual(GuardianLink.objects.count(),2)

    def test_rich_text_typed_dates_and_formula_cached_value_only(self):
        raw=ods()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:xml=z.read('content.xml').decode()
        xml=xml.replace('Nombre Alumno','Nombre<text:s/>Alumno')
        xml=xml.replace('<table:table-cell office:value-type="string"><text:p>2018-01-02</text:p></table:table-cell>','<table:table-cell office:value-type="date" office:date-value="2018-01-02"><text:p>02/01/18</text:p></table:table-cell>')
        xml=xml.replace('<text:p>Persona</text:p>','<text:p>Persona<text:s text:c="2"/><text:span>ficticia</text:span></text:p>')
        xml=xml.replace('<text:p>600000001</text:p>','<text:p>600000001</text:p><text:annotation>IGNORE_THIS</text:annotation>')
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('mimetype','application/vnd.oasis.opendocument.spreadsheet');z.writestr('content.xml',xml)
        payload=parse_ods(out.getvalue());self.assertEqual(payload['rows'][0]['birth'],'2018-01-02')
        self.assertEqual(payload['rows'][0]['name'],'Persona  ficticia Ficticia Uno');self.assertNotIn('IGNORE_THIS',str(payload))
