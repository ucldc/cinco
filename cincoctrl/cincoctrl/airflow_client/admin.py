from django.contrib import admin

from .models import JobRun
from .models import JobTrigger

# Register your models here.


class JobRunInlineAdmin(admin.StackedInline):
    model = JobRun
    extra = 0
    max_num = 0
    fields = ("display_status", "related_model")
    readonly_fields = fields


@admin.register(JobTrigger)
class JobTriggerAdmin(admin.ModelAdmin):
    def job_run_status(self, obj):
        if obj.jobrun_set.all():
            return obj.jobrun_set.all().first().display_status()
        return "No Job Run"

    list_display = (
        "__str__",
        "rest_api_status_code",
        "related_model",
        "job_run_status",
    )
    inlines = [JobRunInlineAdmin]
    readonly_fields = (
        "rest_api_status_code",
        "related_model",
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
                    "related_model",
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

    list_display = (
        "__str__",
        "display_status",
        "related_model",
    )
    readonly_fields = (
        "rest_api_status_code",
        "related_model",
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
                    "related_model",
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
