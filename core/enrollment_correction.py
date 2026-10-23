"""Correction of a recent accidental enrollment, never deletion of a student."""
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from core.access import require_admin
from core.models import Enrollment, Attendance, Learning, ChallengeProgress, Evidence, Audit


def correction_error(enrollment):
    if enrollment.ends is not None:
        return _('No se puede retirar una matrícula finalizada mediante esta corrección.')
    if enrollment.created_at < timezone.now() - timedelta(hours=24):
        return _('Esta corrección solo admite matrículas creadas en las últimas 24 horas. Solicita una revisión administrativa para matrículas anteriores.')
    for model in (Attendance, Learning, ChallengeProgress, Evidence):
        if model.objects.filter(student_id=enrollment.student_id, session__group_id=enrollment.group_id).exists():
            return _('Hay asistencia, aprendizaje, retos o evidencias en este grupo. No se permite retirar la matrícula; revisa el historial antes de corregirla.')
    return ''


@transaction.atomic
def remove_accidental_enrollment(user, enrollment_id, expected_version, confirmation):
    require_admin(user)
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment_id)
    if confirmation != 'RETIRAR':
        raise ValidationError(_('Confirma escribiendo RETIRAR. Solo se elimina la matrícula errónea, no la ficha del alumno.'))
    if expected_version != str(enrollment.version):
        raise ValidationError(_('La matrícula ha cambiado. Recarga la página y revisa antes de continuar.'))
    error = correction_error(enrollment)
    if error:
        raise ValidationError(error)
    student_id = enrollment.student_id
    # Stable student/group identifiers only. No names, contacts or educational content.
    Audit.objects.create(actor=user, action='enrollment:remove-error',
                         object_id=f'{student_id}:{enrollment.group_id}')
    enrollment.delete()
    return student_id
