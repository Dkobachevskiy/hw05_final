from django.test import TestCase
from django.test import Client
from .models import Post, Group, Comment
from django.contrib.auth import get_user_model 
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image, ImageDraw
from django.core.files.base import File
from django.core.cache import cache


User = get_user_model() 


class TestStringMethods(TestCase):

    def setUp(self):
        self.client = Client()
        self.client1 = Client()
        self.user = User.objects.create_user(
                username="sarah", email="connor@skynet.com", password="12345"
        )
        self.group = Group.objects.create(
            title="terminator", 
            slug="film",
            description="1984, science fiction, action"
            )
        self.client.force_login(self.user)     

    def test_profile(self):
        response = self.client.get(reverse('profile', kwargs={"username": self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        response = self.client.get(reverse('profile', kwargs={"username": self.user.username}))
        self.assertEqual(len(response.context["page"]), 0)
        response_create = self.client.post(reverse('new_post'), {"text":"new post", "group": self.group.id}, follow=True)
        self.assertRedirects(response_create, reverse('index'))
        response1 = self.client.get(reverse('profile', kwargs={"username": self.user.username}))
        self.assertEqual(len(response1.context["page"]), 1)
        self.post = Post.objects.get(id=1)
        self.assertEqual(self.post.text, "new post")
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.group, self.group)
        
    def test_guest(self):
        response_new = self.client1.get(reverse('new_post'), follow=True)
        self.assertRedirects(response_new, f"{reverse('login')}?next={reverse('new_post')}")
        self.assertEqual(Post.objects.count(), 0)

    def test_new_post(self):
        newpost = Post.objects.create(
            text="New test post", 
            author=self.user
            )
        cache.clear()
        self.url_list = (
            reverse('index'),
            reverse('profile', kwargs={"username": self.user.username}),
            reverse('post', kwargs={"username": self.user.username, "post_id": newpost.id,})
        )
        for url in self.url_list:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, newpost.text)

    def test_change_post(self):
        self.post = Post.objects.create(
            text="Its driving me crazy!", 
            author=self.user,
            group=self.group
            )
        post = Post.objects.get(author=self.user.id)
        response = self.client.post(
            reverse('post_edit',
            kwargs={'username': self.user.username, 'post_id': self.post.id}
            ),
            { 'text': 'New post text', 'author': self.user.id},
            follow=False
        )
        post_new = Post.objects.get(author=self.user.id)
        self.url_list = (
            reverse('index'),
            reverse('profile', kwargs={"username": self.user.username}),
            reverse('post', kwargs={"username": self.user.username, "post_id": post.id,})
        )
        cache.clear()
        for url in self.url_list:
            with self.subTest(url=url):
                response = self.client.get(url)
            self.assertContains(response, post_new.text)

    def test_404(self):
        response = self.client.get('/auth/test404')
        self.assertEqual(response.status_code, 404)

    def test_with_picture(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        img = SimpleUploadedFile(
            name='some.gif',
            content=small_gif,
            content_type='image/gif',
        )
        post = Post.objects.create(
            author = self.user,
            text = 'text',
            group = self.group,
            image = img,
        )
        cache.clear()
        urls = [
            reverse('index'),
            reverse('profile', kwargs={"username": self.user.username}),
            reverse('post', kwargs={"username": self.user.username, "post_id": post.id,}),
            reverse('group_posts', kwargs={'slug': post.group.slug}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, '<img')

    def test_without_picture(self):
        not_image = SimpleUploadedFile(
            name='some.txt',
            content=b'abc',
            content_type='text/plain',
        )

        url = reverse('new_post')
        response = self.client.post(
            url, {'text': 'some_text', 'image': not_image}
        )

        self.assertFormError(
            response,
            'form',
            'image',
            errors=(
                'Загрузите правильное изображение. '
                'Файл, который вы загрузили, поврежден '
                'или не является изображением.'
            ),
        )

    def test_cache(self):
        response = self.client.get(reverse('index'))
        self.post = Post.objects.create(
            text="Its driving me crazy!", 
            author=self.user,
            group=self.group
            )
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, self.post.text)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, self.post.text)

    def test_folowing_auth_user(self):
        self.client_fol = Client()
        self.user_follow = User.objects.create_user(
                username="user_fol", email="user_fol@skynet.com", password="12345"
        )
        self.client_fol.force_login(self.user_follow)
        self.assertEqual(self.user.following.count(), 0)
        response = self.client_fol.post(reverse('profile_follow', kwargs={'username':self.user.username}))
        self.assertEqual(self.user.following.count(), 1)
        response = self.client_fol.post(reverse('profile_unfollow', kwargs={'username':self.user.username}))
        self.assertEqual(self.user.following.count(), 0)

    def test_new_post_followers(self):
        self.client_fol = Client()
        self.user_follow = User.objects.create_user(
                username="user_fol", email="user_fol@skynet.com", password="12345"
        )
        self.client_fol.force_login(self.user_follow)

        self.client_not_fol = Client()
        self.user_not_follow = User.objects.create_user(
                username="user_fol1", email="user_fol1@skynet.com", password="12345"
        )
        self.client_not_fol.force_login(self.user_not_follow)
        newpost = Post.objects.create(
            text="New test post", 
            author=self.user
            )
        response_fol = self.client_fol.get(reverse('follow_index'))
        response_notfol = self.client_not_fol.get(reverse('follow_index'))
        self.assertNotContains(response_fol, newpost.text)
        self.assertNotContains(response_notfol, newpost.text)
        response_following = self.client_fol.post(
            reverse('profile_follow', kwargs={'username':self.user.username})
        )
        response_fol = self.client_fol.get(reverse('follow_index'))
        response_notfol = self.client_not_fol.get(reverse('follow_index'))
        self.assertContains(response_fol, newpost.text)
        self.assertNotContains(response_notfol, newpost.text)

    def test_auth_user_comment(self):
        self.post = Post.objects.create(
            text="Test post for comments", 
            author=self.user,
            )
        post = Post.objects.get(author=self.user.id)
        self.client_auth = Client()
        self.user_auth = User.objects.create_user(
                username="auth_user", email="auth_user@skynet.com", password="12345"
        )
        self.client_auth.force_login(self.user_auth)
        self.client_not_auth = Client()
        self.assertEqual(Comment.objects.count(),0)
        self.client_auth.post(
            reverse('add_comment', args=[post.author, post.id]),
            {'text': 'new_comment'},
            follow=True
        )
        self.assertEqual(Comment.objects.count(),1)
        self.client_not_auth.post(
            reverse('add_comment', args=[post.author, post.id]),
            {'text': 'new_comment_not_auth'},
            follow=True
        )
        self.assertEqual(Comment.objects.count(),1)
