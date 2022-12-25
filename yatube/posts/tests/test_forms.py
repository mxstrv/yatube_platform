import shutil
import tempfile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateTest(TestCase):
    def setUp(self) -> None:
        self.authorized_user = User.objects.create(username='test_username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.authorized_user)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test description',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create(self):
        """Проверка создания поста с картинкой."""
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content_type='image/jpeg',
            content=b'\x47\x49\x46\x38\x39'
                    b'\x61\x01\x00\x01\x00'
                    b'\x00\x00\x00\x21\xf9\x04'
                    b'\x01\x0a\x00\x01\x00'
                    b'\x2c\x00\x00\x00\x00'
                    b'\x01\x00\x01\x00\x00\x02'
                    b'\x02\x4c\x01\x00\x3b'
        )
        form_data = {
            'text': 'some random text',
            'group': self.group.pk,
            'image': image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'test_username'}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.authorized_user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/test_image.jpg')

    def test_post_edit(self):
        """Проверка редактирования поста."""
        # Создаем пост и группу
        first_post = Post.objects.create(
            text='test text',
            author=self.authorized_user,
            group=self.group,
        )
        group2 = Group.objects.create(
            title='Test group number 2',
            slug='test_slug_2',
            description='Test description for second group',
        )
        # Редактируем пост и добавляем картинку
        edited_post_data = {
            'text': 'some edited random text',
            'group': group2.pk,
            'image': SimpleUploadedFile(
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
        }

        self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': first_post.id}), data=edited_post_data)
        post = Post.objects.last()
        self.assertEqual(post.text, edited_post_data['text'])
        self.assertEqual(post.author, self.authorized_user)
        self.assertEqual(post.group.id, edited_post_data['group'])
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.filter(
            group_id=self.group.pk).count(), 0)

    def test_comments(self):
        """Проверка создания комментария авторизованным пользователем
        и гостем."""
        Post.objects.create(
            text='test text',
            author=self.authorized_user,
            group=self.group,
        )

        # Пишем комментарий к первому посту
        self.authorized_client.post(
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
                             '/auth/login/?next=/posts/1/comment/')
        self.assertEqual(Comment.objects.count(), 1)
