from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group
from django.contrib.auth import get_user_model
from http import HTTPStatus

User = get_user_model()


class PostURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()

        self.authorized_user = User.objects.create(username='test_username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

        self.authorized_user_2 = User.objects.create(
            username='test_username_2'
        )
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.authorized_user_2)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )
        Post.objects.create(
            text='Test text',
            author_id=1,
            group_id=1,
        )
        cls.urls = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_username/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def test_urls_templates_authorized(self):
        """Проверка доступности страниц и
        шаблонов для авторизованного пользователя."""
        templates_urls = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_username/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for path, template in templates_urls.items():
            with self.subTest(address=path):
                response = self.authorized_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_urls_templates_unauthorized(self):
        """Проверка URL и шаблонов для гостя."""
        templates_urls = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_username/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        for path, template in templates_urls.items():
            with self.subTest(address=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_login_required_unauthorized(self):
        """Проверка URL для гостя, в которых необходима авторизация"""
        templates_urls = {
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for path, template in templates_urls.items():
            with self.subTest(address=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response, f'/auth/login/?next={path}')

    def test_post_edit_redirect(self):
        """Проверка редиректа при редактировании поста
        несоответствующим пользователем."""
        response = self.authorized_client_2.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': 1}))
