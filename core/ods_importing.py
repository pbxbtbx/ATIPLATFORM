"""Lectura acotada de ODS y planificación revisable. Nunca ejecuta fórmulas ni enlaces."""
import io
import re
import zipfile
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

TABLE='urn:oasis:names:tc:opendocument:xmlns:table:1.0'
TEXT='urn:oasis:names:tc:opendocument:xmlns:text:1.0'
OFFICE='urn:oasis:names:tc:opendocument:xmlns:office:1.0'
MAX_ROWS=300


def key(value):
    return ' '.join(unicodedata.normalize('NFKC',value).casefold().split())


def cell_value(cell):
    if cell.get(f'{{{OFFICE}}}value-type')=='date':
        return cell.get(f'{{{OFFICE}}}date-value','')[:10]
    def rich_text(node,depth=0):
        if depth>40:raise ValidationError(_('El texto de una celda tiene demasiados niveles de formato.'))
        if node.tag==f'{{{TEXT}}}s':
            try:count=int(node.get(f'{{{TEXT}}}c','1'))
            except ValueError:raise ValidationError(_('Espaciado de celda no válido.'))
            if not 1<=count<=2000:raise ValidationError(_('Espaciado de celda no válido.'))
            return ' '*count
        if node.tag in (f'{{{TEXT}}}tab',f'{{{TEXT}}}line-break'):return ' '
        parts=[node.text or ''];size=len(parts[0])
        for child in node:
            part=rich_text(child,depth+1)+(child.tail or '');size+=len(part)
            if size>2000:raise ValidationError(_('Una celda supera el límite de 2000 caracteres.'))
            parts.append(part)
        return ''.join(parts)
    texts=[];size=0
    for paragraph in cell.findall(f'{{{TEXT}}}p'):
        part=rich_text(paragraph);size+=len(part)+1
        if size>2001:raise ValidationError(_('Una celda supera el límite de 2000 caracteres.'))
        texts.append(part)
    value=' '.join(texts).strip()
    if not value:
        value=cell.get(f'{{{OFFICE}}}string-value','') or cell.get(f'{{{OFFICE}}}value','')
        if cell.get(f'{{{OFFICE}}}value-type')=='float' and value:
            try:
                number=Decimal(value)
                if number.is_finite() and number==number.to_integral_value() and abs(number)<10**20:value=str(int(number))
            except InvalidOperation:pass
    if len(value)>2000:raise ValidationError(_('Una celda supera el límite de 2000 caracteres.'))
    return value.strip()


def birth_value(value):
    if not value:return ''
    from datetime import datetime
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y'):
        try:return datetime.strptime(value,fmt).date().isoformat()
        except ValueError:pass
    return value  # Visible y corregible; nunca adivinar una fecha inválida.


def parse_ods(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos=archive.infolist()
            if len(infos)>300 or sum(i.file_size for i in infos)>20*1024*1024:raise ValueError()
            if archive.read('mimetype').strip()!=b'application/vnd.oasis.opendocument.spreadsheet':raise ValueError()
            xml=archive.read('content.xml')
            if b'\x00' in xml or b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():raise ValueError()
            root=ET.fromstring(xml)
    except (zipfile.BadZipFile,KeyError,ValueError,ET.ParseError,RuntimeError,NotImplementedError):
        raise ValidationError(_('El archivo no es un ODS válido o excede los límites de seguridad.'))
    sheets=[];rows=[];group_sources=[]
    spreadsheet=root.find(f'.//{{{OFFICE}}}spreadsheet')
    if spreadsheet is None:raise ValidationError(_('El archivo no contiene una hoja de cálculo ODS.'))
    for sheet_index,table in enumerate(spreadsheet.findall(f'{{{TABLE}}}table')):
        if sheet_index>=30:raise ValidationError(_('El límite es de 30 pestañas por archivo.'))
        label=table.get(f'{{{TABLE}}}name','')[:150] or str(sheet_index+1)
        columns=None;sheet_rows=[];row_number=0;ignored=0
        for row in table.findall(f'{{{TABLE}}}table-row'):
            try:repeat=int(row.get(f'{{{TABLE}}}number-rows-repeated','1'))
            except ValueError:raise ValidationError(_('Repetición de filas no válida.'))
            if repeat<1 or repeat>1048576:raise ValidationError(_('Repetición de filas no válida.'))
            row_number+=repeat
            cells=[]
            for cell in row:
                if cell.tag not in (f'{{{TABLE}}}table-cell',f'{{{TABLE}}}covered-table-cell'):continue
                try:count=int(cell.get(f'{{{TABLE}}}number-columns-repeated','1'))
                except ValueError:raise ValidationError(_('Repetición de columnas no válida.'))
                if count<1 or count>1048576:raise ValidationError(_('Repetición de columnas no válida.'))
                # Solo las primeras 64 columnas; no expandir relleno de Calc ni leer pagos/notas.
                cells.extend([cell]*min(count,max(0,64-len(cells))))
                if len(cells)>=64:break
            if columns is None:
                headers=[key(cell_value(c)) for c in cells]
                if 'nombre alumno' not in headers or 'apellido alumno' not in headers:continue
                columns={h:i for i,h in enumerate(headers) if h and h not in ('concatenado','concatenar')}
                continue
            def value(header):
                index=columns.get(header)
                return cell_value(cells[index]) if index is not None and index<len(cells) else ''
            first=value('nombre alumno');last=value('apellido alumno')
            if key(first)=='nombre alumno' and key(last)=='apellido alumno':continue
            if not first or not last:
                ignored+=1;continue
            if repeat>1:raise ValidationError(_('Hay filas de alumnado repetidas. Expándelas y revísalas en la hoja antes de importar.'))
            if len(rows)>=MAX_ROWS:raise ValidationError(_('El límite es de 300 alumnos por archivo ODS.'))
            source_group=value('form grupo')[:300]
            source={'sheet':str(sheet_index),'label':source_group}
            if source not in group_sources:group_sources.append(source)
            contacts=[]
            for n in (1,2):
                name=' '.join(v for v in (value(f'nombre resp{n}'),value(f'apellido resp{n}')) if v)
                email=value(f'email resp{n}')
                phone=value(f'tel resp {n}') or value(f'tel resp{n}')
                if name or email or phone:contacts.append({'name':name,'email':email,'phone':phone})
            item={'id':str(len(rows)),'sheet':str(sheet_index),'row':row_number,'name':' '.join(v for v in (first,last) if v),
                  'birth':birth_value(value('date nacimiento') or value('datenacimiento')),'group':str(group_sources.index(source)),'contacts':contacts}
            rows.append(item);sheet_rows.append(item['id'])
        sheets.append({'id':str(sheet_index),'name':label,'rows':len(sheet_rows),'supported':columns is not None,'ignored':ignored})
    if not rows:raise ValidationError(_('No hay alumnado reconocible. Se necesitan las columnas Nombre Alumno y Apellido Alumno.'))
    return {'sheets':sheets,'rows':rows,'groups':group_sources}


def contact_key(contact):
    return (key(contact['name']),key(contact['email']),re.sub(r'[^0-9]','',contact['phone']))
