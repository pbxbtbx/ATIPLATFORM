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
    ROLES = [('admin','Administración'),('teacher','Docente'),('coordinator','Coordinación'),('developer','Desarrollo')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    role = models.CharField(max_length=20,choices=ROLES,default='teacher')
    sensitive_access = models.BooleanField(default=False)
    development_access = models.BooleanField(default=False)
    theme = models.CharField('Estilo visual',max_length=16,choices=[('rpg','Fantasía RPG'),('classic','Atigra claro'),('night','Noche tranquila')],default='rpg')

class AcademicYear(Record):
    name = models.CharField('Nombre',max_length=100)
    starts = models.DateField('Inicio')
    ends = models.DateField('Fin')
    archived = models.BooleanField('Archivado',default=False)
    def __str__(self): return self.name

class ClassGroup(Record):
    TYPES = [('initial','Inicial'),('intermediate','Intermedio'),('durcal','Dúrcal')]
    name = models.CharField('Nombre',max_length=150)
    kind = models.CharField('Tipo',max_length=20,choices=TYPES)
    year = models.ForeignKey(AcademicYear,verbose_name='Curso académico',on_delete=models.PROTECT)
    location = models.CharField('Ubicación',max_length=180,blank=True)
    teachers = models.ManyToManyField(settings.AUTH_USER_MODEL,verbose_name='Docentes / coordinación',blank=True)
    schedule = models.CharField('Horario habitual (informativo)',max_length=200,blank=True)
    starts = models.DateField('Inicio')
    ends = models.DateField('Fin')
    capacity = models.PositiveIntegerField('Capacidad',default=12,validators=[MinValueValidator(1)])
    plan = models.TextField('Planificación',blank=True)
    status = models.CharField('Estado',max_length=20,choices=[('active','Activo'),('finished','Finalizado'),('archived','Archivado')],default='active')
    def __str__(self): return self.name

class Student(Record):
    name = models.CharField('Nombre y apellidos',max_length=200)
    preferred_name = models.CharField('Nombre preferido',max_length=100,blank=True)
    birth_date = models.DateField('Fecha de nacimiento',null=True,blank=True)
    joined = models.DateField('Fecha de incorporación')
    status = models.CharField('Estado',max_length=20,choices=[('active','Activo'),('temporary','Baja temporal'),('left','Baja')],default='active')
    contact = models.CharField('Contacto necesario',max_length=200,blank=True)
    custom_values = models.JSONField(default=dict,blank=True)
    interests = models.TextField('Intereses y proyectos deseados',blank=True)
    experience = models.TextField('Experiencia previa',blank=True)
    strengths = models.TextField('Fortalezas observadas',blank=True)
    preferences = models.TextField('Preferencias y objetivos personales',blank=True)
    strategies = models.TextField('Estrategias, apoyos y adaptaciones educativas',blank=True)
    def __str__(self): return self.name

class Enrollment(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='enrollments')
    group = models.ForeignKey(ClassGroup,on_delete=models.PROTECT,related_name='enrollments')
    starts = models.DateField('Inicio')
    ends = models.DateField('Fin',null=True,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','group'],condition=models.Q(ends=None),name='one_active_enrollment')]

class Guardian(Record):
    name = models.CharField('Nombre y apellidos',max_length=200)
    phone = models.CharField('Teléfono',max_length=60,blank=True)
    email = models.EmailField('Correo',blank=True)
    def __str__(self): return self.name

class GuardianLink(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='guardians')
    guardian = models.ForeignKey(Guardian,verbose_name='Responsable',on_delete=models.PROTECT)
    relationship = models.CharField('Relación',max_length=100)
    priority = models.BooleanField('Contacto prioritario',default=False)
    legal = models.BooleanField('Tutor legal',default=False)
    emergency = models.BooleanField('Contacto de emergencia',default=False)
    pickup = models.CharField('Alcance de autorización de recogida',max_length=250,blank=True)
    notes = models.TextField('Observaciones operativas',blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['student','guardian'],name='guardian_link_unique')]

class Resource(Record):
    title = models.CharField('Título',max_length=200)
    kind = models.CharField('Tipo de clase',max_length=20,choices=ClassGroup.TYPES)
    domain = models.CharField('Ámbito',max_length=120)
    description = models.TextField('Descripción')
    goals = models.TextField('Objetivos',blank=True)
    prerequisites = models.TextField('Requisitos previos',blank=True)
    duration = models.PositiveIntegerField('Duración estimada (minutos)',default=60)
    materials = models.TextField('Materiales',blank=True)
    instructions = models.TextField('Instrucciones y enlaces',blank=True)
    challenges = models.TextField('Retos y ampliaciones por dificultad',blank=True)
    supports = models.TextField('Variantes y apoyos',blank=True)
    criteria = models.TextField('Criterios de observación',blank=True)
    def __str__(self): return self.title

class Sequence(Record):
    name = models.CharField('Nombre',max_length=200)
    resources = models.ManyToManyField(Resource,verbose_name='Recursos',blank=True)
    group = models.ForeignKey(ClassGroup,verbose_name='Grupo',on_delete=models.PROTECT)
    snapshot = models.JSONField(default=list,blank=True)
    def __str__(self): return self.name

class Session(Record):
    STATES = [('planned','Planificada'),('done','Realizada'),('cancelled','Cancelada'),('recover','Pendiente de recuperar')]
    group = models.ForeignKey(ClassGroup,verbose_name='Grupo',on_delete=models.PROTECT)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL,verbose_name='Docente',on_delete=models.PROTECT)
    title = models.CharField('Título',max_length=200)
    number = models.PositiveIntegerField('Número de sesión',default=1)
    start = models.DateTimeField('Inicio')
    end = models.DateTimeField('Fin')
    series = models.UUIDField(null=True,blank=True)
    recovery_of = models.ForeignKey('self',null=True,blank=True,on_delete=models.PROTECT,related_name='recoveries')
    resource = models.ForeignKey(Resource,verbose_name='Recurso de biblioteca',null=True,blank=True,on_delete=models.PROTECT)
    resource_snapshot = models.JSONField(default=dict,blank=True)
    goals = models.TextField('Objetivos',blank=True)
    materials = models.TextField('Materiales y preparación',blank=True)
    planned = models.TextField('Actividades previstas y retos de distintos niveles',blank=True)
    actual = models.TextField('Actividades realizadas y completadas',blank=True)
    pending = models.TextField('Pendiente de retomar',blank=True)
    adaptations = models.TextField('Adaptaciones aplicadas',blank=True)
    notes = models.TextField('Observaciones internas',blank=True)
    next_steps = models.TextField('Próximos pasos',blank=True)
    status = models.CharField('Estado',max_length=20,choices=STATES,default='planned')
    def __str__(self): return self.title

class Holiday(Record):
    title = models.CharField('Festivo / periodo sin clase',max_length=200)
    start = models.DateField('Desde')
    end = models.DateField('Hasta')
    def __str__(self): return self.title

class Attendance(Record):
    STATES = [('present','Presente'),('absent','Ausencia'),('justified','Ausencia justificada'),('late','Retraso'),('early','Salida anticipada')]
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    student = models.ForeignKey(Student,on_delete=models.PROTECT)
    status = models.CharField(max_length=20,choices=STATES)
    note = models.CharField(max_length=250,blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['session','student'],name='attendance_unique')]

class Learning(Record):
    STATES = [('new','Sin iniciar'),('progress','En proceso'),('supported','Completado con apoyo'),('autonomous','Completado con autonomía'),('resume','Pendiente de retomar')]
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='learning')
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    challenge = models.CharField('Reto / proyecto trabajado',max_length=200)
    objective = models.TextField('Objetivo',blank=True)
    evidence = models.TextField('Evidencia observable',blank=True)
    achievement = models.TextField('Logros',blank=True)
    difficulty = models.TextField('Dificultades',blank=True)
    support = models.TextField('Apoyos y adaptaciones',blank=True)
    student_comment = models.TextField('Comentario del alumno',blank=True)
    next_step = models.TextField('Próximo paso',blank=True)
    internal_notes = models.TextField('Notas internas (excluidas de informes familiares)',blank=True)
    activity_status = models.CharField('Actividad',max_length=20,choices=STATES,default='progress')
    learning_status = models.CharField('Aprendizaje demostrado',max_length=20,choices=STATES,default='progress')
    rubric = models.JSONField('Observaciones de rúbrica',default=dict,blank=True)
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
    kind = models.CharField('Naturaleza',max_length=20,choices=[('reported','Hecho comunicado'),('observation','Observación docente'),('unverified','Interpretación por contrastar'),('health','Instrucciones de salud')])
    content = models.TextField('Información pertinente')
    source = models.CharField('Fuente',max_length=150)
    relevance = models.TextField('Finalidad y relevancia educativa u operativa')
    support = models.TextField('Apoyos acordados',blank=True)
    review = models.DateField('Fecha de revisión')
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)

class Consent(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='consents')
    purpose = models.CharField('Finalidad específica',max_length=200)
    text_version = models.CharField('Versión del texto',max_length=100)
    granted_at = models.DateField('Fecha')
    withdrawn_at = models.DateField('Retirada',null=True,blank=True)
    image_use = models.BooleanField('Autorización específica de imágenes',default=False)

class Evidence(Record):
    student = models.ForeignKey(Student,on_delete=models.PROTECT,related_name='evidences')
    session = models.ForeignKey(Session,on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    title = models.CharField('Título',max_length=200)
    file = models.FileField('Archivo privado',upload_to='evidence/%Y/%m',blank=True)
    url = models.URLField('Enlace externo (no se visita automáticamente)',blank=True)
    visibility = models.CharField('Visibilidad',max_length=20,choices=[('staff','Equipo autorizado'),('family','Seleccionable para informe familiar')],default='staff')

class Task(Record):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    title = models.CharField('Recordatorio (sin datos sensibles)',max_length=200)
    due = models.DateField('Fecha')
    done = models.BooleanField('Completado',default=False)

class ConfigVersion(Record):
    STATES = [('draft','Borrador'),('preview','Vista previa validada'),('published','Publicada')]
    environment = models.CharField(max_length=20)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    description = models.CharField('Descripción del cambio',max_length=250)
    payload = models.JSONField('Configuración JSON')
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
