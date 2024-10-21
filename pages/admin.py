from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import PikiPage


class PikiPageAdmin(SimpleHistoryAdmin):
    list_display = ('rel_path', 'tags', 'deleted')
    history_list_display = ('rel_path', 'tags', 'deleted')
    search_fields = ('rel_path', 'tags', )
    list_filter = (
        ('deleted', admin.BooleanFieldListFilter),
    )
    ordering = ["rel_path"]


admin.site.register(PikiPage, PikiPageAdmin)
