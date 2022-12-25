from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, POST_REQUIREMENT_LENGTH

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Lorem ipsum dolor sit amet, consectetur adipiscing elit. '
                 'Fusce vulputate.',
        )

    def test_models_have_correct_object_names(self):
        """Проверка метода __str__ в моделях."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_values = {
            post.text[:POST_REQUIREMENT_LENGTH]: post.__str__(),
            group.title: group.__str__(),
        }
        for model, expected_value in expected_values.items():
            with self.subTest():
                self.assertEqual(model, expected_value)
