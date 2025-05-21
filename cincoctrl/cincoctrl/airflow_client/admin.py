from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import JobRun
from .models import JobTrigger

# Register your models here.


def _link_related_models(related_models):
    model = settings.AIRFLOW_JOB_RELATED_MODEL.lower().replace(".", "_")
    links = []
    for related_model in related_models:
        change_url = reverse(f"admin:{model}_change", args=(related_model.pk,))
        link_str = f'<a href="{change_url}">{related_model!s}</a>'
        links.append(link_str)
    return mark_safe(", ".join(links))  # noqa: S308


def _abbrev_related_models(related_models):
    if related_models.all().count() > 1:
        return {str(related_models.first())} + "..."
    if related_models.all().count() == 1:
        return str(related_models.first())
    return "-"


class JobRunInlineAdmin(admin.TabularInline):
    model = JobRun
    extra = 0
    max_num = 0
    fields = ("dag_run_id", "logical_date", "display_status")
    readonly_fields = fields


@admin.register(JobTrigger)
class JobTriggerAdmin(admin.ModelAdmin):
    def job_run_status(self, obj):
        if obj.jobrun_set.all():
            return obj.jobrun_set.all().first().display_status()
        return "No Job Run"

    @admin.display(description="Related Models")
    def abbrev_related_models(self, obj):
        return _abbrev_related_models(obj.related_models)

    @admin.display(description="Related Models")
    def link_related_models(self, obj):
        return _link_related_models(obj.related_models.all())

    list_display = (
        "__str__",
        "rest_api_status_code",
        "abbrev_related_models",
        "job_run_status",
    )
    inlines = [JobRunInlineAdmin]
    readonly_fields = (
        "rest_api_status_code",
        "link_related_models",
        "dag_id",
        "dag_run_id",
        "logical_date",
        "rest_api_response",
        "dag_run_airflow_url",
        "dag_run_conf",
    )
    fieldsets = (
        (
            "Trigger Request Information",
            {
                "fields": (
                    "dag_id",
                    "dag_run_conf",
                    "link_related_models",
                    "dag_run_airflow_url",
                ),
            },
        ),
        (
            "Trigger Response Information",
            {
                "fields": (
                    "dag_run_id",
                    "logical_date",
                    "rest_api_status_code",
                    "rest_api_response",
                ),
            },
        ),
    )


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    def rest_api_status_code(self, obj):
        if obj.job_trigger:
            return obj.job_trigger.rest_api_status_code
        return "-"

    def rest_api_response(self, obj):
        if obj.job_trigger:
            return obj.job_trigger.rest_api_response
        return "-"

    @admin.display(description="Related Models")
    def abbrev_related_models(self, obj):
        return _abbrev_related_models(obj.related_models)

    @admin.display(description="Related Models")
    def link_related_models(self, obj):
        return _link_related_models(obj.related_models.all())

    list_display = (
        "__str__",
        "display_status",
        "abbrev_related_models",
    )
    readonly_fields = (
        "rest_api_status_code",
        "link_related_models",
        "dag_id",
        "dag_run_id",
        "logical_date",
        "rest_api_response",
        "dag_run_airflow_url",
        "dag_run_conf",
        "job_trigger",
        "display_status",
    )
    fieldsets = (
        (
            "Job Run",
            {
                "fields": (
                    "dag_id",
                    "dag_run_conf",
                    "link_related_models",
                    "dag_run_id",
                    "logical_date",
                    "dag_run_airflow_url",
                    "display_status",
                    "status",
                ),
            },
        ),
        (
            "Trigger Information",
            {
                "fields": (
                    "job_trigger",
                    "rest_api_status_code",
                    "rest_api_response",
                ),
            },
        ),
    )
