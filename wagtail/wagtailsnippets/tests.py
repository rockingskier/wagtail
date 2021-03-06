from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from wagtail.tests.utils import login, unittest
from wagtail.tests.models import Advert

from wagtail.wagtailsnippets.views.snippets import get_content_type_from_url_params, get_snippet_edit_handler
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

class TestSnippetIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_index'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_displays_snippet(self):
        self.assertContains(self.get(), "Adverts")


class TestSnippetListView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_list',
                                       args=('tests', 'advert')),
                               params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_displays_add_button(self):
        self.assertContains(self.get(), "Add advert")


class TestSnippetCreateView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_create',
                                       args=('tests', 'advert')),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets_create',
                               args=('tests', 'advert')),
                               post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_create_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be created due to errors.")
        self.assertContains(response, "This field is required.")

    def test_create(self):
        response = self.post(post_data={'text': 'test_advert',
                                        'url': 'http://www.example.com/'})
        self.assertEqual(response.status_code, 302)

        snippets = Advert.objects.filter(text='test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/')


class TestSnippetEditView(TestCase):
    def setUp(self):
        self.test_snippet = Advert()
        self.test_snippet.text = 'test_advert'
        self.test_snippet.url = 'http://www.example.com/'
        self.test_snippet.save()

        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailsnippets_edit',
                                       args=('tests', 'advert', self.test_snippet.id)),
                               params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailsnippets_edit',
                                        args=('tests', 'advert', self.test_snippet.id)),
                                post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_non_existant_model(self):
        response = self.client.get(reverse('wagtailsnippets_edit',
                                            args=('tests', 'foo', self.test_snippet.id)))
        self.assertEqual(response.status_code, 404)

    def test_nonexistant_id(self):
        response = self.client.get(reverse('wagtailsnippets_edit',
                                            args=('tests', 'advert', 999999)))
        self.assertEqual(response.status_code, 404)

    def test_edit_invalid(self):
        response = self.post(post_data={'foo': 'bar'})
        self.assertContains(response, "The snippet could not be saved due to errors.")
        self.assertContains(response, "This field is required.")

    def test_edit(self):
        response = self.post(post_data={'text': 'edited_test_advert',
                                        'url': 'http://www.example.com/edited'})
        self.assertEqual(response.status_code, 302)

        snippets = Advert.objects.filter(text='edited_test_advert')
        self.assertEqual(snippets.count(), 1)
        self.assertEqual(snippets.first().url, 'http://www.example.com/edited')


class TestSnippetDelete(TestCase):
    def setUp(self):
        self.test_snippet = Advert()
        self.test_snippet.text = 'test_advert'
        self.test_snippet.url = 'http://www.example.com/'
        self.test_snippet.save()

        login(self.client)

    def test_delete_get(self):
        response = self.client.get(reverse('wagtailsnippets_delete', args=('tests', 'advert', self.test_snippet.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        post_data = {'foo': 'bar'} # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailsnippets_delete', args=('tests', 'advert', self.test_snippet.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the page is gone
        self.assertEqual(Advert.objects.filter(text='test_advert').count(), 0)


class TestSnippetChooserPanel(TestCase):
    def setUp(self):
        content_type = get_content_type_from_url_params('tests',
                                                        'advert')

        test_snippet = Advert()
        test_snippet.text = 'test_advert'
        test_snippet.url = 'http://www.example.com/'
        test_snippet.save()

        edit_handler_class = get_snippet_edit_handler(Advert)
        form_class = edit_handler_class.get_form_class(Advert)
        form = form_class(instance=test_snippet)

        self.snippet_chooser_panel_class = SnippetChooserPanel('text', content_type)
        self.snippet_chooser_panel = self.snippet_chooser_panel_class(instance=test_snippet,
                                                                      form=form)

    def test_create_snippet_chooser_panel_class(self):
        self.assertEqual(self.snippet_chooser_panel_class.__name__, '_SnippetChooserPanel')

    def test_render_as_field(self):
        self.assertTrue('test_advert' in self.snippet_chooser_panel.render_as_field())

    def test_render_js(self):
        self.assertTrue("createSnippetChooser(fixPrefix('id_text'), 'contenttypes/contenttype');"
                        in self.snippet_chooser_panel.render_js())
