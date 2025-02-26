from django.forms import ModelForm
from django.forms import Textarea
from django.forms import inlineformset_factory

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import RevisionHistory
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.users.models import Repository


class FindingAidForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ["repository", "ead_file"]
        labels = {"ead_file": "Choose XML File"}

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("queryset", Repository.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["ead_file"].required = True
        self.fields["repository"].queryset = qs
        # TODO: if count == 1 don't show


SuppFileInlineFormSet = inlineformset_factory(
    FindingAid,
    SupplementaryFile,
    fields=["title", "pdf_file"],
    extra=1,
)


class ExpressFindingAidForm(ModelForm):
    class Meta:
        model = FindingAid
        fields = ["repository", "collection_title", "collection_number"]

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop("queryset", Repository.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["repository"].queryset = qs
        # TODO: if count == 1 don't show


class ExpressRecordForm(ModelForm):
    class Meta:
        model = ExpressRecord
        fields = [
            "title_filing",
            "date",
            "start_year",
            "end_year",
            "extent",
            "abstract",
            "scopecontent",
            "language",
            "bioghist",
            "accessrestrict",
            "userestrict",
            "preferred_citation",
            "acqinfo",
            "processing_information",
            "author_statement",
            "online_items_url",
        ]
        widgets = {
            "extent": Textarea(attrs={"rows": 1}),
            "abstract": Textarea(attrs={"rows": 3}),
            "scopecontent": Textarea(attrs={"rows": 3}),
            "bioghist": Textarea(attrs={"rows": 3}),
            "accessrestrict": Textarea(attrs={"rows": 1}),
            "userestrict": Textarea(attrs={"rows": 1}),
            "preferred_citation": Textarea(attrs={"rows": 1}),
            "acqinfo": Textarea(attrs={"rows": 1}),
            "processing_information": Textarea(attrs={"rows": 1}),
            "author_statement": Textarea(attrs={"rows": 1}),
            "online_items_url": Textarea(attrs={"rows": 1}),
        }


CreatorInlineFormSet = inlineformset_factory(
    ExpressRecord,
    ExpressRecordCreator,
    fields=["creator_type", "value"],
    widgets={
        "value": Textarea(attrs={"rows": 1}),
    },
    extra=1,
)

SubjectInlineFormSet = inlineformset_factory(
    ExpressRecord,
    ExpressRecordSubject,
    fields=["subject_type", "value"],
    widgets={
        "value": Textarea(attrs={"rows": 1}),
    },
    extra=1,
)

RevisionInlineFormSet = inlineformset_factory(
    ExpressRecord,
    RevisionHistory,
    fields=["note"],
    widgets={
        "note": Textarea(attrs={"rows": 1}),
    },
    extra=1,
)
