from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe

from cincoctrl.airflow_client.models import JobRun
from cincoctrl.airflow_client.models import JobTrigger
from cincoctrl.findingaids.management.commands.bulk_index_finding_aids import (
    bulk_index_finding_aids,
)
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
    def dag_run_id(self, obj):
        change_url = reverse(
            "admin:airflow_client_jobrun_change",
            args=(obj.jobrun_id,),
        )
        link_str = f'<a href="{change_url}">{obj.jobrun.dag_run_id}</a>'
        return mark_safe(link_str)  # noqa: S308

    def display_status(self, obj):
        return obj.jobrun.display_status()

    def dag_run_conf(self, obj):
        return obj.jobrun.dag_run_conf

    def logical_date(self, obj):
        return obj.jobrun.logical_date

    def dag_id(self, obj):
        return obj.jobrun.dag_id

    def job_trigger(self, obj):
        return obj.jobrun.job_trigger

    model = JobRun.related_models.through
    extra = 0
    max_num = 0
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
    list_filter = ["status", "repository__name", "record_type"]
    actions = ["bulk_index_action"]

    @admin.action(description="Bulk index selected finding aids")
    def bulk_index_action(self, request, queryset):
        job_trigger = bulk_index_finding_aids(queryset)

        message = job_trigger
        if isinstance(job_trigger, JobTrigger):
            change_url = reverse(
                "admin:airflow_client_jobtrigger_change",
                args=(job_trigger.id,),
            )
            link_str = f'Job <a href="{change_url}">{job_trigger}</a> triggered'
            message = mark_safe(link_str)  # noqa: S308

        self.message_user(request, message, messages.SUCCESS)


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
    list_filter = ["finding_aid__status", "finding_aid__repository__name"]


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
