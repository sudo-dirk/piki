from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import PikiPage
from .forms import GroupForm, PermForm

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group


class PikiPageAdmin(SimpleHistoryAdmin):
    list_display = ('rel_path', 'tags', 'group', 'other_perms_read', 'other_perms_write')
    history_list_display = ('rel_path', 'tags', 'deleted')
    search_fields = ('rel_path', 'tags', )
    list_filter = (
        ('group', admin.RelatedFieldListFilter),
        ('other_perms_read', admin.BooleanFieldListFilter),
        ('other_perms_write', admin.BooleanFieldListFilter),
    )
    ordering = ["rel_path"]
    actions = ["remove_access_others", "set_group", "set_perms", ]

    @admin.action(description="Remove access for others")
    def remove_access_others(self, request, query_set):
        query_set.update(other_perms_read=False, other_perms_write=False)

    @admin.action(description="Set group for pages")
    def set_group(self, request, queryset):
        if 'apply' in request.POST:
            if request.POST.get("group"):
                group = Group.objects.get(id=request.POST.get("group"))
            else:
                group = None
            queryset.update(group=group)
            self.message_user(request, "Changed group for {} pages".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        return render(request, 'admin/set_group.html', context={'pages': queryset, 'form': GroupForm()})

    @admin.action(description="Set permissions")
    def set_perms(self, request, queryset):
        if 'apply' in request.POST:
            keys = ["owner_perms_read", "owner_perms_write", "group_perms_read", "group_perms_write", "other_perms_read", "other_perms_write"]
            perms = {key: key in request.POST for key in keys}
            queryset.update(**perms)
            self.message_user(request, "Changed permissions for {} pages".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())
        return render(request, 'admin/set_perms.html', context={'pages': queryset, 'form': PermForm()})


admin.site.disable_action('delete_selected')
admin.site.register(PikiPage, PikiPageAdmin)
