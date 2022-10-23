"""django_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from post_blog_app import api, views
# from ..post_blog_app import api, views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user_to_confirm_post', api.user_to_confirm_post, name='user_to_confirm_post'),
    path('api/user_to_confirm_get', api.user_to_confirm_get, name='user_to_confirm_get'),
    path('api/user_to_confirm_get_all', api.user_to_confirm_get_all, name='user_to_confirm_get_all'),
    path('api/user_to_confirm_delete', api.user_to_confirm_delete, name='user_to_confirm_delete'),
    path('api/user_to_confirm_update', api.user_to_confirm_update, name='user_to_confirm_update'),

    path('test', views.test, name='test'),
    path('menu', views.menu, name='menu'),

    path('', views.start, name='start'),
    path('login', views.login, name='login'),
    path('confirm/<str:login>', views.confirm, name='confirm'),
    path('logout', views.logout, name='logout'),

    path('create_post', views.create_post, name='create_post'),
    path('edit_post/<str:post_type>/<str:post_id>', views.edit_post, name='edit_post'),
    path('post/<str:post_type>/<str:post_id>', views.post, name='post'),
    path('posts', views.posts, name='posts'),

    path('messages', views.msgs, name='messages'),
    path('send_message/<str:author>', views.send_message, name='send_message'),

    path('authors', views.authors, name='authors'),
    path('author/<str:username>', views.author, name='author')
]
