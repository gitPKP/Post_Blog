from django.db import models
from django.contrib.auth.models import User

from datetime import datetime

# Create your models here.


# User from django.contrib.auth.models
class MyModel(models.Model):
    class Meta:
        abstract = True

    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            self.save()


class UserToConfirm(MyModel):
    login = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    code = models.IntegerField()
    valid_time = models.DateTimeField()


# django.contrib.auth.get_user_model()
class Post(MyModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    background_image = models.CharField(max_length=10000, null=True)
    created = models.DateTimeField(default=datetime.now())
    edited = models.DateTimeField(null=True)


class Paragraph(MyModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    paragraph_number = models.IntegerField()
    paragraph_type = models.CharField(max_length=20)
    paragraph_style_txt = models.CharField(max_length=500, null=True)
    paragraph_style_img = models.CharField(max_length=500, null=True)
    url = models.CharField(max_length=5000, null=True)
    paragraph_content = models.CharField(max_length=2000, null=True)


class PostUnfinished(MyModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default='Nowy post')
    description = models.CharField(max_length=1000, default='Opis')
    background_image = models.CharField(max_length=10000, null=True)
    created = models.DateTimeField(null=True)


class ParagraphUnfinished(MyModel):
    post = models.ForeignKey(PostUnfinished, on_delete=models.CASCADE)
    paragraph_number = models.IntegerField()
    paragraph_type = models.CharField(max_length=20)
    paragraph_style_txt = models.CharField(max_length=500, null=True)
    paragraph_style_img = models.CharField(max_length=500, null=True)
    url = models.CharField(max_length=5000, null=True)
    paragraph_content = models.CharField(max_length=2000, null=True)

    temp_paragraph_type = models.CharField(max_length=20, null=True,)
    temp_paragraph_style_txt = models.CharField(max_length=500, null=True)
    temp_paragraph_style_img = models.CharField(max_length=500, null=True)
    temp_url = models.CharField(max_length=5000, null=True)
    temp_paragraph_content = models.CharField(max_length=2000, null=True)


class Likes(MyModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(default='0')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['post', 'author'], name='unique_post_author_combination'
            )
        ]


class Comments(MyModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comments', on_delete=models.CASCADE, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    created = models.DateTimeField(default=datetime.now())


class CommentsLikes(MyModel):
    comment = models.ForeignKey(Comments, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(default='0')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'author'], name='unique_comment_author_combination'
            )
        ]


class Messages(MyModel):
    sender = models.ForeignKey(User, related_name='sender_author', on_delete=models.CASCADE)
    reciver = models.ForeignKey(User, related_name='reciver_author', on_delete=models.CASCADE)
    created = models.DateTimeField(default=datetime.now())
    seen = models.BooleanField(default=False)
    content = models.CharField(max_length=1000)




"""class MessagesConstraint(Messages):
    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(Messages.sender != Messages.reciver), name='different_sender_reciver')
        ]"""
