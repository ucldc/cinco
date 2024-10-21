import os

from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.forms import formset_factory

from cincoctrl.findingaids.models import File

class FileForm(ModelForm):
    class Meta:
        model = File
        fields = ['file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.types = kwargs.get('types', None)

    def clean_file(self):
        data = self.cleaned_data['file']
        extension = data.split(".")[-1]
        if self.types and not extension in self.types:
            raise ValidationError(f"Expected file extensions: {self.types}")


FileFormSet = formset_factory(FileForm)

# class FindingAidForm(ModelForm):
#     class Meta:
#         models = FindingAid
#         fields = ['collection_title',
#                   'collection_number']

# class ExpressRecordForm(ModelForm):
#     class Meta:
#         model = ExpressRecord
#         fields = ['title_filing', 
#                   'local_identifier',
#                   'date_dacs',
#                   'date_iso',
#                   'extent',
#                   'abstract',
#                   'language',
#                   'accessrestrict',
#                   'userestrict',
#                   'acqinfo',
#                   'scopecontent',
#                   'bioghist',
#                   'online_items_url']
        
# class ExpressRecordFieldForm(ModelForm):
#     class Meta:
#         model = ExpressRecordField
#         fields = ['value']
