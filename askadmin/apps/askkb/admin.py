from django.contrib import admin
from .models import KnowledgeBase, KnowledgeBaseSnippet


class SnippetInline(admin.StackedInline):
    model = KnowledgeBaseSnippet


class KnowledgeBaseAdmin(admin.ModelAdmin):
    inlines = [SnippetInline]
    list_display = ['name', 'id']


admin.site.register(KnowledgeBase, KnowledgeBaseAdmin)