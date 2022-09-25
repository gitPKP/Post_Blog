from django.contrib import admin
from post_blog_app import models

# Register your models here.
admin.site.register(models.UserToConfirm)

admin.site.register(models.Post)
admin.site.register(models.Paragraph)
admin.site.register(models.PostUnfinished)
admin.site.register(models.ParagraphUnfinished)

admin.site.register(models.Likes)
admin.site.register(models.Comments)
admin.site.register(models.CommentsLikes)

admin.site.register(models.Messages)
