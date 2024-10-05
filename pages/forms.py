from typing import Any, Mapping
from django import forms
from django.forms.renderers import BaseRenderer
from django.forms.utils import ErrorList


class EditForm(forms.Form):  # Note that it is not inheriting from forms.ModelForm
    page_txt = forms.CharField(max_length=20000, label="Page source text", widget=forms.Textarea(attrs={"rows": "20"}))

    def __init__(self, *args, **kwargs) -> None:
        page_data = kwargs.pop("page_data")
        super().__init__(*args, **kwargs)
        page_txt = self.fields['page_txt']
        page_txt.initial = page_data
