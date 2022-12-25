from django.core.paginator import Paginator


POSTS_ON_PAGE = 10


def my_paginator(posts, request):
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
