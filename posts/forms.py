from django.forms import ModelForm
from .models import Post, Comment
 

class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
 
form = PostForm()


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Текст комментария'}
        #widgets = {'text': Textarea()}
