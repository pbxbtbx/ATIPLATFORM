from django.core.exceptions import PermissionDenied
from .models import Profile, ClassGroup, Student, Audit

def profile(user):
    p, _ = Profile.objects.get_or_create(user=user)
    return p

def admin(user): return user.is_superuser or profile(user).role == 'admin'
def educational(user): return admin(user) or profile(user).role in ('teacher','coordinator')
def developer(user): return profile(user).development_access

def groups(user):
    if admin(user): return ClassGroup.objects.all()
    if not educational(user): return ClassGroup.objects.none()
    return ClassGroup.objects.filter(teachers=user)

def students(user):
    if admin(user): return Student.objects.all()
    return Student.objects.filter(enrollments__group__in=groups(user)).distinct()

def require_admin(user):
    if not admin(user): raise PermissionDenied

def require_developer(user):
    if not developer(user): raise PermissionDenied

def require_sensitive(user, student):
    if not profile(user).sensitive_access or not students(user).filter(pk=student.pk).exists(): raise PermissionDenied

def audit(user, action, obj=None):
    Audit.objects.create(actor=user,action=action,object_id=str(obj.pk) if obj else '')
