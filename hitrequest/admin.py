from django.contrib import admin
from .models import Document, AudioSnippet

# Register your models here.

class DocumentAdmin(admin.ModelAdmin):
    pass

class AudioSnippetAdmin(admin.ModelAdmin):
    pass

admin.site.register(Document, DocumentAdmin)
admin.site.register(AudioSnippet, AudioSnippetAdmin)
