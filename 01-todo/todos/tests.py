from django.test import TestCase
from django.urls import reverse
from .models import Todo


class TodoModelTests(TestCase):
    def test_todo_creation_sets_fields(self):
        t = Todo.objects.create(title='Buy milk', description='2 liters')
        self.assertFalse(t.resolved)
        self.assertIsNotNone(t.created_at)
        self.assertIsNotNone(t.updated_at)

    def test_todo_str_returns_title(self):
        t = Todo.objects.create(title='Read book')
        self.assertEqual(str(t), 'Read book')


class TodoViewTests(TestCase):
    def setUp(self):
        self.todo = Todo.objects.create(title='Task 1')

    def test_todo_list_view_shows_todos(self):
        res = self.client.get(reverse('todo_list'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'todos/home.html')
        self.assertContains(res, 'Task 1')

    def test_todo_create_get_shows_form(self):
        res = self.client.get(reverse('todo_create'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'todos/todo_form.html')

    def test_todo_create_post_creates_and_redirects(self):
        res = self.client.post(reverse('todo_create'), {'title': 'New Task', 'description': 'desc'})
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Todo.objects.filter(title='New Task').exists())

    def test_todo_edit_updates_todo(self):
        url = reverse('todo_edit', args=[self.todo.pk])
        res = self.client.post(url, {'title': 'Updated', 'description': 'new'})
        self.assertEqual(res.status_code, 302)
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, 'Updated')

    def test_todo_delete_removes_todo(self):
        url = reverse('todo_delete', args=[self.todo.pk])
        # GET confirms
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'todos/todo_confirm_delete.html')
        # POST deletes
        res = self.client.post(url)
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Todo.objects.filter(pk=self.todo.pk).exists())

    def test_todo_resolve_marks_resolved(self):
        url = reverse('todo_resolve', args=[self.todo.pk])
        res = self.client.get(url)
        # our resolve view redirects
        self.assertEqual(res.status_code, 302)
        self.todo.refresh_from_db()
        self.assertTrue(self.todo.resolved)

    def test_urls_reverse_correctly(self):
        # ensure reversing works for all named urls
        reverse('todo_list')
        reverse('todo_create')
        reverse('todo_edit', args=[self.todo.pk])
        reverse('todo_delete', args=[self.todo.pk])
        reverse('todo_resolve', args=[self.todo.pk])

    def test_home_template_contains_action_links(self):
        res = self.client.get(reverse('todo_list'))
        self.assertContains(res, reverse('todo_create'))
        self.assertContains(res, reverse('todo_edit', args=[self.todo.pk]))
        self.assertContains(res, reverse('todo_delete', args=[self.todo.pk]))
from django.test import TestCase

# Create your tests here.
