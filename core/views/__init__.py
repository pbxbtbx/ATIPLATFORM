"""Vistas organizadas por dominio. Conserva las rutas públicas existentes."""
from .dashboard import home, task_add, task_done
from .groups import group_list, group_detail, group_edit
from .students import student_list, student_edit, student_detail, enrollment, guardian_edit, restricted_edit, consent_add, student_export
from .planning import calendar_view, session_edit, session_detail, class_save, recover_session
from .library import library, resource_edit, sequence_edit
from .evidence import evidence_add, evidence_download
from .reports import reports, group_report
from .administration import settings_view, admin_form, user_add, user_edit
from .development import developer_view, config_preview, config_restore
from .appearance import appearance

from .notifications import notifications, task_toggle
from .language import set_language

from .imports import import_start, import_preview, import_template

from .planning import challenge_edit, session_delete
from .students import support_plan_edit
from .ods import ods_preview

from .practice import practice_view
from .accessibility import accessibility_view

from .security import security_view

from .students import enrollment_remove

from .suggestions import student_suggestions, group_suggestions
