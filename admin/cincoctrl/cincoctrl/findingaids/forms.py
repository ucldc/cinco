from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.forms import formset_factory

from cincoctrl.findingaids.models import File


class FileForm(ModelForm):
    class Meta:
        model = File
        fields = ["file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.types = kwargs.get("types")

    def clean_file(self):
        data = self.cleaned_data["file"]
        extension = data.split(".")[-1]
        if self.types and extension not in self.types:
            m = f"Expected file extensions: {self.types}"
            raise ValidationError(m)


FileFormSet = formset_factory(FileForm)
