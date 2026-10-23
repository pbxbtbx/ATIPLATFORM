from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Profile, AcademicYear, ClassGroup, Student, Enrollment


class ListFilterTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('filters.admin'); Profile.objects.create(user=self.admin, role='admin')
        self.teacher = User.objects.create_user('filters.teacher'); Profile.objects.create(user=self.teacher, role='teacher')
        self.dev = User.objects.create_user('filters.dev'); Profile.objects.create(user=self.dev, role='developer', development_access=True)
        today = timezone.localdate()
        self.year = AcademicYear.objects.create(name='Curso visible', starts=today-timedelta(days=30), ends=today+timedelta(days=60))
        self.hidden_year = AcademicYear.objects.create(name='Curso ajeno', starts=self.year.starts, ends=self.year.ends)
        self.group = ClassGroup.objects.create(name='INICIO MIÉRCOLES', kind='initial', year=self.year, location='Sede visible', schedule='Miércoles 16:30–18:00', starts=self.year.starts, ends=self.year.ends)
        self.group.teachers.add(self.teacher)
        self.second = ClassGroup.objects.create(name='INTERMEDIO MARTES', kind='intermediate', year=self.year, location='Sede visible', starts=self.year.starts, ends=self.year.ends)
        self.foreign = ClassGroup.objects.create(name='GRUPO OCULTO', kind='durcal', year=self.hidden_year, location='Ubicación ajena', status='archived', starts=self.year.starts, ends=self.year.ends)
        self.one = Student.objects.create(name='ÁNGELA LÓPEZ FICTICIA', preferred_name='Luna', joined=today)
        self.two = Student.objects.create(name='Nombre de prueba', joined=today, status='temporary')
        self.hidden = Student.objects.create(name='Persona oculta', joined=today)
        Enrollment.objects.create(student=self.one, group=self.group, starts=today)
        Enrollment.objects.create(student=self.one, group=self.second, starts=today)
        Enrollment.objects.create(student=self.two, group=self.group, starts=today, ends=today)
        Enrollment.objects.create(student=self.hidden, group=self.foreign, starts=today)
        self.client.force_login(self.admin)

    def ids(self, response, key):
        self.assertEqual(response.status_code, 200)
        return {obj.pk for obj in response.context[key]}

    def test_student_search_tokens_accents_preferred_and_escape(self):
        for query in ('angela', 'lopez angela', 'LUNA', '  áNgElA  '):
            self.assertEqual(self.ids(self.client.post('/students/', {'q': query}), 'students_list'), {self.one.pk})
        response = self.client.post('/students/', {'q': '<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')
        self.assertEqual(response.context['result_count'], 0)
        self.assertEqual(self.ids(self.client.get('/students/', {'q': 'luna'}), 'students_list'), {self.one.pk})

    def test_student_group_and_state_combined_deduplicate_and_reset(self):
        self.assertEqual(self.ids(self.client.post('/students/', {'group': str(self.group.pk)}), 'students_list'), {self.one.pk})
        self.assertEqual(self.ids(self.client.post('/students/', {'status': 'temporary'}), 'students_list'), {self.two.pk})
        self.assertEqual(self.ids(self.client.post('/students/', {'group': str(self.group.pk), 'status': 'temporary'}), 'students_list'), set())
        response = self.client.get('/students/')
        self.assertEqual(response.context['result_count'], 3)
        self.assertEqual(len(list(response.context['students_list'])), 3)
        self.assertContains(response, 'Limpiar filtros')

    def test_group_search_combined_filters_and_order(self):
        response = self.client.post('/groups/', {'q': 'miercoles 16:30', 'kind': 'initial', 'year': str(self.year.pk), 'location': 'Sede visible', 'status': 'active', 'order': 'name'})
        self.assertEqual(self.ids(response, 'groups_list'), {self.group.pk})
        self.assertEqual(self.ids(self.client.post('/groups/', {'status': 'archived'}), 'groups_list'), {self.foreign.pk})
        response = self.client.post('/groups/', {'order': 'kind'})
        self.assertEqual([obj.kind for obj in response.context['groups_list']], ['durcal', 'initial', 'intermediate'])
        self.assertEqual(self.client.get('/groups/').context['result_count'], 3)

    def test_permissions_filter_options_results_counts_and_tampering(self):
        self.client.force_login(self.teacher)
        for route in ('/groups/', '/students/'):
            response = self.client.get(route)
            self.assertNotContains(response, self.foreign.name)
            self.assertNotContains(response, self.hidden.name)
            self.assertNotContains(response, self.hidden_year.name)
            self.assertNotContains(response, self.foreign.location)
        for values in ({'year': str(self.hidden_year.pk)}, {'location': self.foreign.location}, {'order': 'teachers__password'}, {'kind': 'unknown'}):
            self.assertEqual(self.ids(self.client.post('/groups/', values), 'groups_list'), set())
        self.assertEqual(self.ids(self.client.post('/students/', {'group': str(self.foreign.pk)}), 'students_list'), set())
        self.assertEqual(self.ids(self.client.post('/students/', {'q': self.hidden.name}), 'students_list'), set())
        self.client.force_login(self.dev)
        self.assertEqual(self.client.get('/groups/').context['result_count'], 0)
        self.assertEqual(self.client.get('/students/').context['result_count'], 0)

    def test_post_csrf_private_responses_no_url_names_no_mutation(self):
        before = {m.__name__: list(m.objects.values()) for m in (Student, Enrollment, ClassGroup)}
        csrf = Client(enforce_csrf_checks=True); csrf.force_login(self.admin)
        for route in ('/students/', '/groups/'):
            self.assertEqual(csrf.post(route, {'q': 'test'}).status_code, 403)
            response = self.client.post(route, {'q': 'test'})
            self.assertEqual(response['Cache-Control'], 'private, no-store')
            self.assertContains(response, 'method="post"')
            self.assertNotIn('Location', response)
        self.assertEqual(before, {m.__name__: list(m.objects.values()) for m in (Student, Enrollment, ClassGroup)})
        self.client.logout()
        self.assertEqual(self.client.get('/groups/').status_code, 302)
        self.assertEqual(self.client.get('/students/').status_code, 302)

    def test_invalid_or_overlong_query_is_safe_and_preserved(self):
        for route, key in (('/groups/', 'groups_list'), ('/students/', 'students_list')):
            response = self.client.post(route, {'q': 'x'*151})
            self.assertEqual(self.ids(response, key), set())
            self.assertTrue(response.context['list_filters'].errors)
            self.assertEqual(response.context['list_filters']['q'].value(), 'x'*151)
