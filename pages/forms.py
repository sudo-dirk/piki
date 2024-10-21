from typing import Any, Mapping
from django import forms
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList

from .models import PikiPage


class EditForm(forms.ModelForm):
    class Meta:
        model = PikiPage
        fields = [
            "page_txt",
            "tags",
            "owner", "owner_perms_read", "owner_perms_write",
            "group", "group_perms_read", "group_perms_write",
            "other_perms_read", "other_perms_write",]


class RenameForm(forms.Form):  # Note that it is not inheriting from forms.ModelForm
    page_name = forms.CharField(max_length=500, label="Change the page name:", required=True)

    def __init__(self, *args, **kwargs) -> None:
        page_name = kwargs.pop("page_name")
        super().__init__(*args, **kwargs)
        self.fields['page_name'].initial = page_name
