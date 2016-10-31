from django import forms

class DocumentForm(forms.Form):
    uploadedFile = forms.FileField(
        label='Select a file',
        help_text='max. 42 megabytes'
    )
