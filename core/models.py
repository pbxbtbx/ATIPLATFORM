from django.utils.translation import gettext_lazy as _, pgettext_lazy
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)
    class Meta:
        abstract = True

class Profile(models.Model):
    ROLES = [('admin',_('Administración')),('teacher',_('Docente')),('coordinator',_('Coordinación')),('developer',_('Desarrollo'))]
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    role = models.CharField(max_length=20,choices=ROLES,default='teacher')
    sensitive_access = models.BooleanField(default=False)
    development_access = models.BooleanField(default=False)
    language = models.CharField(_('Idioma'),max_length=2,choices=[('es',_('Español')),('en','English')],default='es')
    theme = models.CharField(_('Estilo visual'),max_length=16,choices=[('rpg',_('Fantasía RPG')),('classic',_('Atigra claro')),('night',_('Noche tranquila'))],default='rpg')

class AcademicYear(Record):
    name = models.CharField(_('Nombre'),max_length=100)
    starts = models.DateField(pgettext_lazy('date_field','Inicio'))
    ends = models.DateField(_('Fin'))
    archived = models.BooleanField(_('Archivado'),default=False)
    def __str__(self): return self.name

class ClassGroup(Record):
    TYPES = [('initial',_('Inicial')),('intermediate',_('Intermedio')),('durcal',_('Dúrcal'))]
    name = models.CharField(_('Nombre'),max_length=150)
    kind = models.CharField(_('Tipo'),max_length=20,choices=TYPES)
    year = models.ForeignKey(AcademicYear,verbose_name=_('Curso académico'),on_delete=models.PROTECT)
    location = models.CharField(_('Ubicación'),max_length=180,blank=True)
    teachers = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name=_('Docentes / coordinación'),blank=True)
    schedule = models.CharField(_('Horario habitual (informativo)'),max_length=200,blank=True)
    starts = models.DateField(pgettext_lazy('date_field','Inicio'))
    ends = models.DateField(_('Fin'))
    capacity = models.PositiveIntegerField(_('Capacidad'),default=12,validators=[MinValueValidator(1)])
    plan = models.TextField(_('Planificación'),blank=True)
    status = models.CharField(_('Estado'),max_length=20,choices=[('active',_('Activo')),('finished',_('Finalizado')),('archived',_('Archivado'))],default='active')
    def __str__(self): return self.name

class Student(Record):
    name = models.CharField(_('Nombre y apellidos'),max_length=200)
    preferred_name = models.CharField(_('Nombre preferido'),max_length=100,blank=True)
    birth_date = models.DateField(_('Fecha de nacimiento'),null=True,blank=True)
    joined = models.DateField(_('Fecha de incorporación'))
    status = models.CharField(_('Estado'),max_length=20,choices=[('active',_('Activo')),('temporary',_('Baja temporal')),('left',_('Baja'))],default='active')
    contact = models.CharField(_('Contacto necesario'),max_length=200,blank=True)
    custom_values = models.JSONField(default=dict,blank=True)
    interests = models.TextField(_('Intereses y proyectos deseados'),blank=True)
    experience = models.TextField(_('Experiencia previa'),blank=True)
    strengths = models.TextField(_('Fortalezas observadas'),blank=True)
    preferences = models.TextField(_('Preferencias y objetivos personales'),blank=True)
    strategies = models.TextField(_('Estrategias, apoyos y adaptaciones educativas'),blank=True)
    def __str__(self): return self.name

class Enrollment(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='enrollments')
    group = models.ForeignKey(ClassGroup,on_delete=models.PROTECT,related_name='enrollments')
    starts = models.DateField(pgettext_lazy('date_field','Inicio'))
    ends = models.DateField(_('Fin'),null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','group'],condition=models.Q(ends=None),name='one_active_enrollment')]

class Guardian(Record):
    name = models.CharField(_('Nombre y apellidos'),max_length=200)
    phone = models.CharField(_('Teléfono'),max_length=60,blank=True)
    email = models.EmailField(_('Correo'),blank=True)
    def __str__(self): return self.name

class GuardianLink(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='guardians')
    guardian = models.ForeignKey(Guardian,verbose_name=_('Responsable'),on_delete=models.PROTECT)
    relationship = models.CharField(_('Relación'),max_length=100)
    priority = models.BooleanField(_('Contacto prioritario'),default=False)
    legal = models.BooleanField(_('Tutor legal'),default=False)
    emergency = models.BooleanField(_('Contacto de emergencia'),default=False)
    pickup = models.CharField(_('Alcance de autorización de recogida'),max_length=250,blank=True)
    notes = models.TextField(_('Observaciones operativas'),blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','guardian'],name='guardian_link_unique')]

class Resource(Record):
    title = models.CharField(_('Título'),max_length=200)
    kind = models.CharField(_('Tipo de clase'),max_length=20,choices=ClassGroup.TYPES)
    domain = models.CharField(_('Ámbito'),max_length=120)
    description = models.TextField(_('Descripción'))
    goals = models.TextField(_('Objetivos'),blank=True)
    prerequisites = models.TextField(_('Requisitos previos'),blank=True)
    duration = models.PositiveIntegerField(_('Duración estimada (minutos)'),default=60)
    materials = models.TextField(_('Materiales'),blank=True)
    instructions = models.TextField(_('Instrucciones y enlaces'),blank=True)
    challenges = models.TextField(_('Retos y ampliaciones por dificultad'),blank=True)
    supports = models.TextField(_('Variantes y apoyos'),blank=True)
    criteria = models.TextField(_('Criterios de observación'),blank=True)
    def __str__(self): return self.title

class Sequence(Record):
    name = models.CharField(_('Nombre'),max_length=200)
    resources = models.ManyToManyField(Resource,verbose_name=_('Recursos'),blank=True)
    group = models.ForeignKey(ClassGroup,verbose_name=_('Grupo'),on_delete=models.PROTECT)
    snapshot = models.JSONField(default=list,blank=True)
    def __str__(self): return self.name

class Session(Record):
    STATES = [('planned',_('Planificada')),('done',_('Realizada')),('cancelled',_('Cancelada')),('recover',_('Pendiente de recuperar'))]
    group = models.ForeignKey(ClassGroup,verbose_name=_('Grupo'),on_delete=models.PROTECT)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name=_('Docente'),on_delete=models.PROTECT)
    title = models.CharField(_('Título'),max_length=200)
    number = models.PositiveIntegerField(_('Número de sesión'),default=1)
    start = models.DateTimeField(pgettext_lazy('date_field','Inicio'))
    end = models.DateTimeField(_('Fin'))
    series = models.UUIDField(null=True,blank=True)
    recovery_of = models.ForeignKey('self',null=True,blank=True,on_delete=models.PROTECT,related_name='recoveries')
    resource = models.ForeignKey(Resource,verbose_name=_('Recurso de biblioteca'),null=True,blank=True,on_delete=models.PROTECT)
    resource_snapshot = models.JSONField(default=dict,blank=True)
    goals = models.TextField(_('Objetivos'),blank=True)
    materials = models.TextField(_('Materiales y preparación'),blank=True)
    planned = models.TextField(_('Actividades previstas y retos de distintos niveles'),blank=True)
    actual = models.TextField(_('Actividades realizadas y completadas'),blank=True)
    pending = models.TextField(_('Pendiente de retomar'),blank=True)
    adaptations = models.TextField(_('Adaptaciones aplicadas'),blank=True)
    notes = models.TextField(_('Observaciones internas'),blank=True)
    next_steps = models.TextField(_('Próximos pasos'),blank=True)
    status = models.CharField(_('Estado'),max_length=20,choices=STATES,default='planned')
    def __str__(self): return self.title

class Holiday(Record):
    title = models.CharField(_('Festivo / periodo sin clase'),max_length=200)
    start = models.DateField(_('Desde'))
    end = models.DateField(_('Hasta'))
    def __str__(self): return self.title

class Attendance(Record):
    STATES = [('present',_('Presente')),('absent',_('Ausencia')),('justified',_('Ausencia justificada')),('late',_('Retraso')),('early',_('Salida anticipada'))]
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    student = models.ForeignKey(Student,on_delete=models.PROTECT)
    status = models.CharField(max_length=20,choices=STATES)
    note = models.CharField(max_length=250,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['session','student'],name='attendance_unique')]

class Learning(Record):
    STATES = [('new',_('Sin iniciar')),('progress',_('En proceso')),('supported',_('Completado con apoyo')),('autonomous',_('Completado con autonomía')),('resume',_('Pendiente de retomar'))]
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='learning')
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    challenge = models.CharField(_('Reto / proyecto trabajado'),max_length=200)
    objective = models.TextField(_('Objetivo'),blank=True)
    evidence = models.TextField(_('Evidencia observable'),blank=True)
    achievement = models.TextField(_('Logros'),blank=True)
    difficulty = models.TextField(_('Dificultades'),blank=True)
    support = models.TextField(_('Apoyos y adaptaciones'),blank=True)
    student_comment = models.TextField(_('Comentario del alumno'),blank=True)
    next_step = models.TextField(_('Próximo paso'),blank=True)
    internal_notes = models.TextField(_('Notas internas (excluidas de informes familiares)'),blank=True)
    activity_status = models.CharField(_('Actividad'),max_length=20,choices=STATES,default='progress')
    learning_status = models.CharField(_('Aprendizaje demostrado'),max_length=20,choices=STATES,default='progress')
    rubric = models.JSONField(_('Observaciones de rúbrica'),default=dict,blank=True)
    state_labels = models.JSONField(default=dict,blank=True)
    supersedes = models.ForeignKey('self',null=True,blank=True,on_delete=models.PROTECT)
    def save(self,*args,**kwargs):
        if self._state.adding and not self.state_labels:
            from .configuration import learning_states
            self.state_labels=dict(learning_states())
        super().save(*args,**kwargs)
    def get_activity_status_display(self): return self.state_labels.get(self.activity_status,dict(self.STATES).get(self.activity_status,self.activity_status))
    def get_learning_status_display(self): return self.state_labels.get(self.learning_status,dict(self.STATES).get(self.learning_status,self.learning_status))


class RestrictedNote(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='restricted_notes')
    kind = models.CharField(_('Naturaleza'),max_length=20,choices=[('reported',_('Hecho comunicado')),('observation',_('Observación docente')),('unverified',_('Interpretación por contrastar')),('health',_('Instrucciones de salud'))])
    content = models.TextField(_('Información pertinente'))
    source = models.CharField(_('Fuente'),max_length=150)
    relevance = models.TextField(_('Finalidad y relevancia educativa u operativa'))
    support = models.TextField(_('Apoyos acordados'),blank=True)
    review = models.DateField(_('Fecha de revisión'))
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

class Consent(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='consents')
    purpose = models.CharField(_('Finalidad específica'),max_length=200)
    text_version = models.CharField(_('Versión del texto'),max_length=100)
    granted_at = models.DateField(_('Fecha'))
    withdrawn_at = models.DateField(_('Retirada'),null=True,blank=True)
    image_use = models.BooleanField(_('Autorización específica de imágenes'),default=False)

class Evidence(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='evidences')
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    title = models.CharField(_('Título'),max_length=200)
    file = models.FileField(_('Archivo privado'),upload_to='evidence/%Y/%m',blank=True)
    url = models.URLField(_('Enlace externo (no se visita automáticamente)'),blank=True)
    visibility = models.CharField(_('Visibilidad'),max_length=20,choices=[('staff',_('Equipo autorizado')),('family',_('Seleccionable para informe familiar'))],default='staff')

class Task(Record):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    title = models.CharField(_('Recordatorio (sin datos sensibles)'),max_length=200)
    due = models.DateField(_('Fecha'))
    done = models.BooleanField(_('Completado'),default=False)

class ConfigVersion(Record):
    STATES = [('draft',_('Borrador')),('preview',_('Vista previa validada')),('published',_('Publicada'))]
    environment = models.CharField(max_length=20)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    description = models.CharField(_('Descripción del cambio'),max_length=250)
    payload = models.JSONField(_('Configuración JSON'))
    state = models.CharField(max_length=20,choices=STATES,default='draft')
    published_at = models.DateTimeField(null=True,blank=True)

class Audit(Record):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100,blank=True)
    # No contents, request payloads, tokens or personal data.

class BackupCheck(Record):
    filename = models.CharField(max_length=200)
    digest = models.CharField(max_length=64)
    verified_at = models.DateTimeField(null=True)

class Release(Record):
    version_name = models.CharField(max_length=50)
    notes = models.TextField()
    deployed_at = models.DateTimeField()

class TechnicalEvent(Record):
    code = models.CharField(max_length=40)
    reference = models.UUIDField(default=uuid.uuid4)
