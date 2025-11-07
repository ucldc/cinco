from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe

from cincoctrl.airflow_client.models import JobRun
from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
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
    search_fields = ["collection_title", "ark", "ead_file"]
    list_display = (
        "collection_title",
        "collection_number",
        "ark",
        "repository",
        "record_type",
        "ead_file",
        "date_updated",
    )
    list_filter = ["status", "record_type", "repository__name"]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    actions = [
        "bulk_index_action",
        "delete_finding_aid_action",
        "unpublish_finding_aid_action",
    ]

    @admin.action(description="Unpublish selected finding aids")
    def unpublish_finding_aid_action(self, request, queryset):
        if settings.ENABLE_AIRFLOW:
            airflow_urls = []
            for finding_aid in queryset:
                airflow_url = trigger_dag(
                    "unpublish_finding_aid",
                    {
                        "finding_aid_ark": finding_aid.ark,
                        "repository_code": finding_aid.repository.code,
                        "cinco_environment": settings.CINCO_ENVIRONMENT,
                    },
                    related_models=[finding_aid],
                    dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__bulk",
                    dag_note=(
                        f"Unpublishing {finding_aid.ark} "
                        f"from {finding_aid.repository.name} "
                        f"({finding_aid.repository.code})"
                    ),
                    track_dag=False,
                )
                airflow_urls.append(airflow_url)
            airflow_urls = "\n".join(airflow_urls)
            self.message_user(
                request,
                f"Unpublishing {queryset.count()} finding aids.\n{airflow_urls}",
                messages.SUCCESS,
            )
        else:
            self.message_user(request, "Airflow is not enabled.", messages.ERROR)

    @admin.action(description="Delete (and unindex) selected finding aids")
    def delete_finding_aid_action(self, request, queryset):
        if settings.ENABLE_AIRFLOW:
            airflow_urls = []
            for finding_aid in queryset:
                airflow_url = trigger_dag(
                    "delete_finding_aid",
                    {
                        "finding_aid_ark": finding_aid.ark,
                        "repository_code": finding_aid.repository.code,
                        "cinco_environment": settings.CINCO_ENVIRONMENT,
                    },
                    dag_note=(
                        f"Deleting {finding_aid.ark} from {finding_aid.repository.name}"
                        f" ({finding_aid.repository.code})"
                    ),
                    related_models=[finding_aid],
                    dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__bulk",
                    track_dag=False,
                )
                airflow_urls.append(airflow_url)

            airflow_urls = "\n".join(airflow_urls)
            self.message_user(
                request,
                f"Deleting {queryset.count()} finding aids.\n{airflow_urls}",
                messages.SUCCESS,
            )
        else:
            self.message_user(request, "Airflow is not enabled.", messages.ERROR)

    @admin.action(description="Index selected finding aids")
    def index_finding_aid_action(self, request, queryset):
        if settings.ENABLE_AIRFLOW:
            airflow_urls = []
            for finding_aid in queryset:
                job_trigger = finding_aid.queue_index()
                airflow_urls.append(job_trigger.dag_run_airflow_url)

            airflow_urls = "\n".join(airflow_urls)
            self.message_user(
                request,
                f"Indexing {queryset.count()} finding aids.\n{airflow_urls}",
                messages.SUCCESS,
            )
        else:
            self.message_user(request, "Airflow is not enabled.", messages.ERROR)


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
