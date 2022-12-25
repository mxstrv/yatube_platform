from http import HTTPStatus
from django.test import TestCase, Client


class PostURLTests(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_urls_templates_authorized(self):
        url_template = {
            '/non-exist-page': 'core/404.html',
        }
        for path, template in url_template.items():
            with self.subTest(address=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, template)
