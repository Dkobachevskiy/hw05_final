from django.contrib import admin 
from .models import Post, Group, Comment
 
 
class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", 'group')
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"
 
class GroupAdmin(admin.ModelAdmin):
    list_display = ("pk", "title", "slug", "description")
    search_field = ("title",)
    empty_value_display = "-пусто-"
# при регистрации модели Post источником конфигурации для неё назначаем класс PostAdmin
class CommentAdmin(admin.ModelAdmin):  
    list_display = ('post', 'text', 'author', 'created')
    

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
