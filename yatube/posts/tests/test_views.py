from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:gen'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                    self.user1.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id':
                    self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id':
                    self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='slug 1',
            description='Тестовое описание',
        )
        Post.objects.create(
            author=cls.user,
            group=cls.group1,
            text='Тестовый пост',
        )

        for i in range(12):
            Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f'Тестовый пост №{i}',
            )

    def test_first_page_contains_ten_records_index(self):
        response = self.client.get(reverse('posts:gen'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_index(self):
        response = self.client.get(reverse('posts:gen') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_group_list(self):
        response = self.client.get(reverse('posts:group_posts', kwargs={'slug':
                                           self.group.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['group'], self.group)

    def test_second_page_contains_three_records_group_list(self):
        response = self.client.get(reverse('posts:group_posts', kwargs={'slug':
                                   self.group.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)
        self.assertEqual(response.context['group'], self.group)

    def test_first_page_contains_ten_records_profile(self):
        response = self.client.get(reverse('posts:profile', kwargs={'username':
                                           self.user.username}))
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['username'], self.user.username)

    def test_second_page_contains_three_records_profile(self):
        response = self.client.get(reverse('posts:profile', kwargs={'username':
                                           self.user.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
        self.assertEqual(response.context['username'], self.user.username)


class PostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Тестовое описание',
        )

        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='slug1',
            description='Тестовое описание1',
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
            image=uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').image, self.post.image)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('short_text'),
                         self.post.text[:30])
        self.assertEqual(response.context.get('count'), 1)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('text'), self.post.text)
        self.assertEqual(response.context.get('is_edit'), True)

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_index_correct_context(self):
        response = self.authorized_client.get(reverse('posts:gen'))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.group.title
        task_text_0 = first_object.text
        task_slug_0 = first_object.group.slug
        task_image_0 = first_object.image
        self.assertEqual(task_title_0, self.group.title)
        self.assertEqual(task_text_0, self.post.text)
        self.assertEqual(task_slug_0, self.group.slug)
        self.assertEqual(task_image_0, self.post.image)

    def test_post_group_list_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                                      kwargs={'slug': 'slug'}))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.group.title
        task_text_0 = first_object.text
        task_slug_0 = first_object.group.slug
        task_image_0 = first_object.image
        self.assertEqual(task_title_0, self.group.title)
        self.assertEqual(task_text_0, self.post.text)
        self.assertEqual(task_slug_0, self.group.slug)
        self.assertEqual(task_image_0, self.post.image)
        self.assertEqual(response.context.get('group'), self.group)

    def test_post_profile_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        first_object = response.context['page_obj'][0]
        task_title_0 = first_object.group.title
        task_text_0 = first_object.text
        task_slug_0 = first_object.group.slug
        task_image_0 = first_object.image
        self.assertEqual(task_title_0, self.group.title)
        self.assertEqual(task_text_0, self.post.text)
        self.assertEqual(task_slug_0, self.group.slug)
        self.assertEqual(task_image_0, self.post.image)
        self.assertEqual(response.context.get('username'), self.user.username)
        self.assertEqual(response.context.get('count'), 1)
        self.assertEqual(response.context.get('author'), self.post.author)

    def test_other_group_correct_context(self):
        response = self.authorized_client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group1.slug}))
        self.assertEqual(len(response.context.get('page_obj')), 0)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.user3 = User.objects.create_user(username='auth3')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.user3)

    def test_new_post_for_follower(self):
        Follow.objects.create(author=self.user2, user=self.user)
        post = Post.objects.create(
            author=self.user2,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context['page_obj'][0], post)

    def test_new_post_for_unfollower(self):
        Post.objects.create(
            author=self.user2,
            text='Тестовый пост',
        )
        response = self.authorized_client3.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class CommentViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.govnopost = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.govnopost
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_comment(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.govnopost.id}))
        self.assertEqual(response.context.get('comments')[0], self.comment)
