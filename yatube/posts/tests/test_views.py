import shutil
import tempfile
import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.db.models.fields.files import ImageFieldFile

from ..models import Post, Group, Comment

User = get_user_model()
POSTS_AMOUNT = 17
PAGINATOR_REQUIRED_AMOUNT = 10
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    def setUp(self) -> None:
        self.authorized_client = User.objects.create(username='test_username')
        self.authorized_user = Client()
        self.authorized_user.force_login(self.authorized_client)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(slug='test-slug', title='test group name')
        # Создаем 17 постов для проверки работы паджинатора
        for post in range(POSTS_AMOUNT):
            Post.objects.create(
                text='Test text',
                author_id=1,
                group_id=1,
                image=SimpleUploadedFile(
                    name='test_image.jpg',
                    content_type='image/jpeg',
                    content=b'\x47\x49\x46\x38\x39'
                            b'\x61\x01\x00\x01\x00'
                            b'\x00\x00\x00\x21\xf9\x04'
                            b'\x01\x0a\x00\x01\x00'
                            b'\x2c\x00\x00\x00\x00'
                            b'\x01\x00\x01\x00\x00\x02'
                            b'\x02\x4c\x01\x00\x3b'
                ),
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_html_templates_views(self):
        """Проверка соответствия view классов ожидаемым шаблонам."""
        templates_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': 'test_username'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse('posts:post_create', ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Проверка контекста для главной страницы."""
        response = self.client.get(reverse('posts:index'))
        objects_received = response.context['page_obj'][0]
        self.assertEqual(objects_received.text, 'Test text')
        self.assertIsInstance(objects_received.image, ImageFieldFile)

    def test_group_list_show_correct_context(self):
        """Проверка group list"""
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test-slug'}))
        objects_received = response.context['page_obj'][0]
        post_text = objects_received.text
        group = objects_received.group.title
        image = objects_received.image
        self.assertEqual(post_text, 'Test text')
        self.assertEqual(group, 'test group name')
        self.assertIsInstance(image, ImageFieldFile)

    def test_profile_page_shows_correct_context(self):
        """Проверка страницы пользователя."""
        response = self.client.get(
            reverse('posts:profile', kwargs={'username': 'test_username'}))
        self.assertEqual(
            response.context.get('author').username, 'test_username')
        # Проверка постов
        for i in range(len(response.context)):
            self.assertEqual(
                response.context.get('posts')[i].text, 'Test text')
            self.assertIsInstance(
                response.context.get('posts')[i].image, ImageFieldFile)

    def test_post_detail_page_shows_correct_context(self):
        """Проверка подробной информации о посте"""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, 'Test text')
        self.assertEqual(response.context.get('title'), 'Test text')
        self.assertEqual(
            response.context.get('author_total_posts'), POSTS_AMOUNT)
        self.assertIsInstance(
            response.context.get('post').image, ImageFieldFile)

    def test_post_edit_page_is_correct(self):
        """Проверка контекста страницы редактирования поста."""
        response = self.authorized_user.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, 'Test text')
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            forms.fields.CharField)
        self.assertIsInstance(
            response.context.get('form').fields.get('group'),
            forms.fields.ChoiceField)
        self.assertEqual(response.context.get('is_edit'), True)
        self.assertIsInstance(response.context.get('form').fields.get('image'),
                              forms.fields.ImageField)

    def test_post_create_show_correct_context(self):
        """Проверка соответствия контекста страницы
         создания поста в передаваемые шаблоны."""
        response = self.authorized_user.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_contain_paginator(self):
        """Проверка работы паджинатора."""
        response_index = self.authorized_user.get(reverse('posts:index'))
        response_group = self.authorized_user.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        response_profile = self.authorized_user.get(reverse(
            'posts:profile', kwargs={'username': 'test_username'}))
        self.assertEqual(len(response_index.context['page_obj']),
                         PAGINATOR_REQUIRED_AMOUNT)
        self.assertEqual(len(response_group.context['page_obj']),
                         PAGINATOR_REQUIRED_AMOUNT)
        self.assertEqual(len(response_profile.context['page_obj']),
                         PAGINATOR_REQUIRED_AMOUNT)

    def test_comments(self):
        """Проверка создания комментария авторизованным пользователем
        и гостем."""
        # Пишем комментарий к первому посту
        self.authorized_user.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data={'text': 'test comment'},
            follow=True,
        )
        comment = Comment.objects.get(post_id=1)
        self.assertEqual(comment.text, 'test comment')

        # Пытаемся написать комментарий неавторизированным пользователем
        guest_comment = self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data={'text': 'test comment by guest'},
            follow=True,
        )
        self.assertRedirects(guest_comment,
                             f'/auth/login/?next=/posts/1/comment/')
        self.assertEqual(Comment.objects.count(), 1)

    def test_follow(self):
    pass




