from django.forms import ModelForm
from django.forms import inlineformset_factory

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import RevisionHistory
from cincoctrl.findingaids.models import SupplementaryFile


class FindingAidForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ["ead_file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ead_file"].required = True


SuppFileInlineFormSet = inlineformset_factory(
    FindingAid,
    SupplementaryFile,
    fields=["pdf_file"],
    extra=1,
)


class ExpressFindingAidForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ["collection_title", "collection_number"]


class ExpressRecordForm(ModelForm):
    class Meta:
        model = ExpressRecord
        exclude = ("finding_aid", "date_created", "date_updated")


CreatorInlineFormSet = inlineformset_factory(
    ExpressRecord,
    ExpressRecordCreator,
    fields=["creator_type", "value"],
    extra=1,
)

SubjectInlineFormSet = inlineformset_factory(
    ExpressRecord,
    ExpressRecordSubject,
    fields=["subject_type", "value"],
    extra=1,
)

RevisionInlineFormSet = inlineformset_factory(
    ExpressRecord,
    RevisionHistory,
    fields=["note"],
    extra=1,
)
