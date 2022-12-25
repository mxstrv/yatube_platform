from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .paginators import my_paginator

POST_DETAIL_FIRST_LETTERS = 30


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = my_paginator(posts, request)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    page_obj = my_paginator(posts, request)
    return render(request, 'posts/group_list.html', {'posts': posts,
                                                     'group': group,
                                                     'page_obj': page_obj, })


def profile(request, username):
    author = User.objects.get(username=username)
    posts = author.posts.select_related('group')
    page_obj = my_paginator(posts, request)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user_id=request.user,
            author_id=author.id,
        ).exists()
    else:
        following = False
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.select_related('group').get(id=post_id)
    title = str(post)[:POST_DETAIL_FIRST_LETTERS]
    author_total_posts = Post.objects.filter(author=post.author).count()
    comment_form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'title': title,
        'author_total_posts': author_total_posts,
        'comments': comments,
        'form': comment_form,

    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.select_related('group').get(id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following_list = Follow.objects.filter(
        user_id=request.user).values_list('author_id')
    posts = Post.objects.select_related('group', 'author').filter(
        author_id__in=following_list)
    page_obj = my_paginator(posts, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user_to_follow = User.objects.get(username=username)
    if (Follow.objects.filter
        (user_id=request.user.id, author_id=user_to_follow.id).exists()
            or request.user.id == user_to_follow.id):
        return redirect('posts:profile', user_to_follow)
    Follow.objects.create(
        user_id=request.user.id,
        author_id=user_to_follow.id)
    return redirect('posts:profile', user_to_follow)


@login_required
def profile_unfollow(request, username):
    user_to_unfollow = User.objects.get(username=username)
    Follow.objects.filter(
        user_id=request.user.id,
        author_id=user_to_unfollow.id).delete()
    return redirect('posts:profile', user_to_unfollow)
