from typing import Any, Mapping
from django import forms
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList


class EditForm(forms.Form):  # Note that it is not inheriting from forms.ModelForm
    page_txt = forms.CharField(max_length=20000, label="Page source text", widget=forms.Textarea(attrs={"rows": "20"}))
    page_tags = forms.CharField(max_length=20000, label="Tags (words separated by spaces)", required=False)

    def __init__(self, *args, **kwargs) -> None:
        page_data = kwargs.pop("page_data")
        page_tags = kwargs.pop("page_tags")
        super().__init__(*args, **kwargs)
        self.fields['page_txt'].initial = page_data
        self.fields['page_tags'].initial = page_tags
