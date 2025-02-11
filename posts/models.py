from django.db import models 
from django.contrib.auth import get_user_model 
from django import forms

  
User = get_user_model() 
  
class Group(models.Model): 
    title = models.CharField(max_length=200) 
    slug = models.SlugField(max_length=75, unique=True) 
    description = models.TextField(max_length=400) 
 
    def __str__(self): 
        return self.title 

  
class Post(models.Model): 
    text = models.TextField("Текс поста")
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author_posts") 
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, blank=True, null=True, 
            related_name="group_posts") 
    image = models.ImageField(upload_to='posts/', blank=True, null=True) 
                                                                                            
    class Meta: 
        ordering = ["-pub_date"]
 
    def __str__(self):
       return self.text


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created = models.DateTimeField("Дата публикации", auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
