from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required 
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page


@cache_page(60 * 1)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )
 
 
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.order_by('-pub_date').all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "group.html",
        {"group": group, "posts":posts, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST, files=request.FILES or None)
    if request.method != 'POST':
        return render(request, 'new.html', {'form':form})
    if form.is_valid():
        post_get = form.save(commit=False)
        post_get.author = request.user
        post_get.save()
        return redirect('index')
    return render(request, 'new.html', {'form':form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.author_posts.all()
    paginator = Paginator(author_posts, 5)
    page = paginator.get_page(request.GET.get('page'))
    following = False
    if request.user.__class__.__name__ != 'AnonymousUser':
        following = Follow.objects.filter(author=author, user=request.user).exists()
    followers_count = Follow.objects.filter(author=author).count
    following_count = Follow.objects.filter(user=author).count
    context = {
        'page': page,
        'paginator': paginator,
        'author': author,
        'following': following,
        'followers_count': followers_count,
        'following_count': following_count,
        'author_posts': author_posts,
        }
    return render(request, 'profile.html', context)
 
 
def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    posts_count = author.author_posts
    items = post.comments.all()
    context = {
        'author_posts': posts_count,
        'post': post,
        'author': author,
        'form': CommentForm(),
        'items': items,
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return post_view(request, username, post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    form_content = {'form': form, 'post': post, 'post_edit': True}
    
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('post', username=post.author, post_id=post.id)
        return render(request, 'new.html', form_content)
    
    return render(request, "new.html", form_content)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username,
                             id=post_id)
    form = CommentForm(request.POST or None)
    items = post.comments.all()
    if form.is_valid():
        comment = form.save(commit=False) 
        comment.post = post 
        comment.author = request.user 
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    context = {
        'form': form,
        'post_author': post_author,
        'post': post,
        'form': CommentForm(),
        'items': items,
    }
    return render(request, 'comments.html', context)

@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page':page,
        'paginator':paginator,
    }
    return render(request, "follow.html", context)

@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        follow = Follow.objects.get_or_create(user=user, author=author)   
    return redirect('profile', username=username)

@login_required
def profile_unfollow(request, username):
    unfollow_profile = Follow.objects.get(author__username=username, user=request.user)
    if Follow.objects.filter(pk=unfollow_profile.pk).exists():
        unfollow_profile.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
