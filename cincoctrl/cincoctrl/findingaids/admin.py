from django.contrib import admin

from cincoctrl.airflow_client.models import JobRun
from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import IndexingHistory
from cincoctrl.findingaids.models import Language
from cincoctrl.findingaids.models import RevisionHistory
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.models import ValidationWarning


class SupplementaryFileInline(admin.TabularInline):
    model = SupplementaryFile


class JobRunInline(admin.TabularInline):
    model = JobRun
    extra = 0
    raw_id_fields = ("related_model",)
    fields = (
        "dag_run_id",
        "display_status",
        "dag_run_conf",
        "logical_date",
        "dag_id",
        "job_trigger",
    )
    readonly_fields = (
        "dag_run_id",
        "display_status",
        "dag_run_conf",
        "logical_date",
        "dag_id",
        "job_trigger",
    )


@admin.register(FindingAid)
class FindingAidAdmin(admin.ModelAdmin):
    inlines = [SupplementaryFileInline, JobRunInline]
    search_fields = ["collection_title", "ark"]
    list_display = ("collection_title", "collection_number", "ark", "repository")
    list_filter = ["status"]


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
    ordering = ("finding_aid", "order")
    list_filter = ["textract_status"]


@admin.register(ExpressRecordSubject)
class ExpressRecordSubjectAdmin(admin.ModelAdmin):
    raw_id_fields = ("record",)


@admin.register(ExpressRecordCreator)
class ExpressRecordCreatorAdmin(admin.ModelAdmin):
    raw_id_fields = ("record",)


@admin.register(IndexingHistory)
class IndexingHistoryAdmin(admin.ModelAdmin):
    pass
