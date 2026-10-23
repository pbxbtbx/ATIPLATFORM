"""Explicit, scoped erasure. No shell, new backup, automatic real/fake inference or legal certification."""
import json
from pathlib import Path
from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.core.files.storage import default_storage
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext as _
from core.access import admin, profile
from core.models import (Student, Enrollment, Guardian, GuardianLink, Attendance, Learning,
    ChallengeProgress, SupportPlan, Consent, RestrictedNote, Evidence, ImportDraft, Audit, DataErasure)

RELATED = (Enrollment, GuardianLink, Attendance, Learning, ChallengeProgress, SupportPlan, Consent, RestrictedNote, Evidence)
SALT = 'atigra.data-erasure.v1'


def require_erasure(user):
    if not admin(user) or not profile(user).sensitive_access:
        raise PermissionDenied


def selections(values):
    import uuid
    try:
        ids = sorted({str(uuid.UUID(str(value))) for value in values})
    except (ValueError, TypeError, AttributeError):
        raise ValidationError(_('Selección no válida.'))
    if not 1 <= len(ids) <= 300 or Student.objects.filter(pk__in=ids).count() != len(ids):
        raise ValidationError(_('Selecciona entre 1 y 300 alumnos existentes.'))
    return ids


def snapshot(ids):
    rows = {'students': list(Student.objects.filter(pk__in=ids).order_by('pk').values())}
    guardian_ids = list(GuardianLink.objects.filter(student_id__in=ids).values_list('guardian_id', flat=True))
    for model in RELATED:
        rows[model._meta.model_name] = list(model.objects.filter(student_id__in=ids).order_by('pk').values())
    rows['guardians'] = list(Guardian.objects.filter(pk__in=guardian_ids).order_by('pk').values())
    rows['guardian_links'] = list(GuardianLink.objects.filter(guardian_id__in=guardian_ids).order_by('pk').values())
    # Every draft is removed: duplicate names/contacts cannot be reliably matched by ID.
    rows['drafts'] = list(ImportDraft.objects.order_by('pk').values())
    orphan_count = Guardian.objects.filter(pk__in=guardian_ids).exclude(guardianlink__student_id__in=Student.objects.exclude(pk__in=ids).values('pk')).count()
    counts = {'students': len(ids), 'guardians': orphan_count, 'shared_guardians': len(set(guardian_ids)) - orphan_count, 'drafts': len(rows['drafts'])}
    counts.update({model._meta.model_name: len(rows[model._meta.model_name]) for model in RELATED})
    digest = salted_hmac(SALT, json.dumps(rows, default=str, sort_keys=True), algorithm='sha256').hexdigest()
    return digest, counts


def make_preview(user, values):
    require_erasure(user)
    ids = selections(values)
    digest, counts = snapshot(ids)
    token = signing.dumps({'ids': ids, 'digest': digest, 'actor': user.pk, 'environment': settings.ENVIRONMENT}, salt=SALT, compress=True)
    return token, counts, Student.objects.filter(pk__in=ids).order_by('name')


def authenticate_erasure(user, password):
    require_erasure(user)
    if not user.check_password(password):
        raise ValidationError(_('La contraseña actual no es correcta. No se ha iniciado el borrado.'))


def load_preview(user, token):
    require_erasure(user)
    try:
        data = signing.loads(token, salt=SALT, max_age=900)
        if data['actor'] != user.pk or data['environment'] != settings.ENVIRONMENT:
            raise ValueError()
        ids = selections(data['ids'])
        return ids, data['digest']
    except (signing.BadSignature, ValueError, TypeError, KeyError):
        raise ValidationError(_('La revisión ha caducado o no es válida. Prepara una selección nueva.'))


@transaction.atomic
def erase_records(user, token, password, confirmation, accepted):
    authenticate_erasure(user, password)
    ids, digest = load_preview(user, token)
    if confirmation != f'ELIMINAR {len(ids)} ALUMNOS' or not accepted:
        raise ValidationError(_('Confirma el alcance y escribe la frase exacta de eliminación.'))
    list(Student.objects.select_for_update().filter(pk__in=ids))
    current_digest, counts = snapshot(ids)
    if current_digest != digest:
        raise ValidationError(_('Los datos han cambiado desde la revisión. No se ha borrado nada; revisa otra vez.'))
    guardian_ids = list(GuardianLink.objects.filter(student_id__in=ids).values_list('guardian_id', flat=True))
    files = sorted(set(Evidence.objects.filter(student_id__in=ids).exclude(file='').values_list('file', flat=True)))
    audit_ids = set(ids)
    for model in RELATED:
        audit_ids.update(str(pk) for pk in model.objects.filter(student_id__in=ids).values_list('pk', flat=True))
    audit_ids.update(str(pk) for pk in ImportDraft.objects.values_list('pk', flat=True))
    # Break revision pointers ONLY within the selected scope. A foreign reference blocks the transaction.
    for model in (Learning, ChallengeProgress, SupportPlan):
        model.objects.filter(student_id__in=ids).update(supersedes=None)
    for model in (Evidence, Learning, ChallengeProgress, SupportPlan, Attendance, Consent, RestrictedNote, Enrollment, GuardianLink):
        model.objects.filter(student_id__in=ids).delete()
    orphan_guardians = Guardian.objects.filter(pk__in=guardian_ids, guardianlink__isnull=True)
    removed_guardians = list(orphan_guardians.values_list('pk', flat=True))
    audit_ids.update(str(pk) for pk in removed_guardians)
    orphan_guardians.delete()
    Student.objects.filter(pk__in=ids).delete()
    ImportDraft.objects.all().delete()
    # Remove minimal technical references to the erased records as well.
    Audit.objects.filter(object_id__in=audit_ids).delete()
    for student_id in ids:
        Audit.objects.filter(object_id__contains=student_id).delete()
    database_ok = not Student.objects.filter(pk__in=ids).exists() and not ImportDraft.objects.exists()
    database_ok = database_ok and all(not model.objects.filter(student_id__in=ids).exists() for model in RELATED)
    database_ok = database_ok and not Guardian.objects.filter(pk__in=removed_guardians).exists()
    if not database_ok:
        raise ValidationError(_('La comprobación de registros ha fallado. La transacción no se ha confirmado.'))
    receipt = DataErasure.objects.create(author=user, counts=counts, pending_files=files,
        checks={'database': True, 'files': False})
    Audit.objects.create(actor=user, action='privacy:erasure', object_id=str(receipt.pk))
    return receipt


def checked_file(name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('file')
    root = Path(settings.MEDIA_ROOT).absolute()
    if root.resolve() != root or not root.is_relative_to(Path(settings.BASE_DIR).resolve() / 'var'):
        raise ValueError('root')
    path = root / name
    if not path.resolve().is_relative_to(root):
        raise ValueError('scope')
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise ValueError('symlink')
        if part == root:
            break
    if Path(default_storage.path(name)).absolute() != path:
        raise ValueError('storage')
    return path


@transaction.atomic
def verify_files(receipt):
    receipt = DataErasure.objects.select_for_update().get(pk=receipt.pk)
    pending = []
    for name in receipt.pending_files:
        try:
            path = checked_file(name)
            # A file still referenced by another person is not silently erased.
            if Evidence.objects.filter(file=name).exists():
                pending.append(name)
                continue
            default_storage.delete(name)
            if path.exists() or default_storage.exists(name):
                pending.append(name)
        except (OSError, ValueError, NotImplementedError):
            pending.append(name)
    receipt.pending_files = pending
    receipt.checks = {**receipt.checks, 'files': not pending}
    receipt.save(update_fields=['pending_files', 'checks', 'updated_at'])
    return receipt


def remaining_copy_checks():
    root = Path(settings.BASE_DIR) / 'var'
    try:
        backups = root / 'backups'
        backup_files = sum(1 for p in backups.rglob('*') if p.is_file()) if not backups.is_symlink() else -1
        main = Path(settings.DATABASES['default']['NAME']).resolve()
        other_databases = sum(1 for p in root.glob('*.sqlite3') if p.resolve() != main)
        return {'backup_files': backup_files, 'other_databases': other_databases}
    except OSError:
        return {'backup_files': -1, 'other_databases': -1}
