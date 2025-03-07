from django.contrib import admin

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.models import RevisionHistory
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.models import ValidationWarning


class SupplementaryFileInline(admin.TabularInline):
    model = SupplementaryFile


@admin.register(FindingAid)
class FindingAidAdmin(admin.ModelAdmin):
    inlines = [SupplementaryFileInline]
    search_fields = ["collection_title", "ark"]
    list_display = ("collection_title", "collection_number", "ark", "repository")


class ExpressRecordCreatorInline(admin.TabularInline):
    model = ExpressRecordCreator


class ExpressRecordSubjectInline(admin.TabularInline):
    model = ExpressRecordSubject


class RevisionHistoryInline(admin.TabularInline):
    model = RevisionHistory


@admin.register(ValidationWarning)
class ValidationWarningAdmin(admin.ModelAdmin):
    pass


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpressRecord)
class ExpressRecordAdmin(admin.ModelAdmin):
    inlines = [
        ExpressRecordCreatorInline,
        ExpressRecordSubjectInline,
        RevisionHistoryInline,
    ]
    search_fields = ["finding_aid__collection_title", "finding_aid__ark"]


@admin.register(SupplementaryFile)
class SupplementaryFileAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpressRecordSubject)
class ExpressRecordSubjectAdmin(admin.ModelAdmin):
    raw_id_fields = ("record",)


@admin.register(ExpressRecordCreator)
class ExpressRecordCreatorAdmin(admin.ModelAdmin):
    raw_id_fields = ("record",)
