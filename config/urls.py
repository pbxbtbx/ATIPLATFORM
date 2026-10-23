from django.urls import path
from django.contrib.auth import views as auth
from core import views as v
urlpatterns=[
path('enrollments/<uuid:pk>/remove-error/',v.enrollment_remove,name='enrollment_remove'),
path('developer/security/',v.security_view,name='security'),
path('accessibility/',v.accessibility_view,name='accessibility'),
path('practice/',v.practice_view,name='practice'),
path('imports/<uuid:pk>/ods/',v.ods_preview,name='ods_preview'),
path('sessions/<uuid:pk>/challenges/',v.challenge_edit,name='challenge_edit'),path('sessions/<uuid:pk>/delete/',v.session_delete,name='session_delete'),path('students/<uuid:pk>/support/',v.support_plan_edit,name='support_plan'),
path('imports/',v.import_start,name='import_start'),path('imports/template/<str:kind>/',v.import_template,name='import_template'),path('imports/<uuid:pk>/',v.import_preview,name='import_preview'),
path('notifications/',v.notifications,name='notifications'),path('notifications/<uuid:pk>/toggle/',v.task_toggle,name='task_toggle'),path('language/',v.set_language,name='set_language'),
path('login/',auth.LoginView.as_view(template_name='core/login.html'),name='login'),path('logout/',auth.LogoutView.as_view(),name='logout'),
path('',v.home,name='home'),path('appearance/',v.appearance,name='appearance'),path('groups/',v.group_list,name='groups'),path('groups/new/',v.group_edit,name='group_new'),path('groups/<uuid:pk>/',v.group_detail,name='group'),path('groups/<uuid:pk>/edit/',v.group_edit,name='group_edit'),
path('students/',v.student_list,name='students'),path('students/new/',v.student_edit,name='student_new'),path('students/<uuid:pk>/',v.student_detail,name='student'),path('students/<uuid:pk>/edit/',v.student_edit,name='student_edit'),path('students/<uuid:pk>/enroll/',v.enrollment,name='enrollment'),path('students/<uuid:pk>/guardian/',v.guardian_edit,name='guardian_link'),path('students/<uuid:pk>/restricted/',v.restricted_edit,name='restricted_new'),path('students/<uuid:pk>/consent/',v.consent_add,name='consent_new'),
path('students/<uuid:pk>/evidence/',v.evidence_add,name='evidence_new'),path('evidence/<uuid:pk>/download/',v.evidence_download,name='evidence_download'),
path('calendar/',v.calendar_view,name='calendar'),path('sessions/new/',v.session_edit,name='session_new'),path('sessions/<uuid:pk>/',v.session_detail,name='session'),path('sessions/<uuid:pk>/edit/',v.session_edit,name='session_edit'),path('sessions/<uuid:pk>/save/',v.class_save,name='class_save'),path('sessions/<uuid:pk>/recover/',v.recover_session,name='session_recover'),
path('library/',v.library,name='library'),path('library/new/',v.resource_edit,name='resource_new'),path('library/<uuid:pk>/edit/',v.resource_edit,name='resource_edit'),path('sequences/new/',v.sequence_edit,name='sequence_new'),path('reports/',v.reports,name='reports'),path('reports/group/',v.group_report,name='group_report'),path('students/<uuid:pk>/export/',v.student_export,name='student_export'),
path('settings/',v.settings_view,name='settings'),path('settings/users/new/',v.user_add,name='user_new'),path('settings/users/<int:pk>/edit/',v.user_edit,name='user_edit'),path('settings/<str:kind>/new/',v.admin_form,name='admin_new'),path('settings/<str:kind>/<uuid:pk>/',v.admin_form,name='admin_edit'),
path('tasks/new/',v.task_add,name='task_new'),path('tasks/<uuid:pk>/done/',v.task_done,name='task_done'),
path('developer/',v.developer_view,name='developer'),path('developer/<uuid:pk>/preview/',v.config_preview,name='config_preview'),path('developer/<uuid:pk>/restore/',v.config_restore,name='config_restore')]
