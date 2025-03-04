from django.contrib import admin

from .models import JobRun
from .models import JobTrigger

# Register your models here.


@admin.register(JobTrigger)
class JobTriggerAdmin(admin.ModelAdmin):
    list_display = (
        "dag_run_id",
        "dag_id",
        "logical_date",
        "rest_api_status_code",
        "related_model",
    )


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = (
        "dag_run_id",
        "display_status",
        "dag_id",
        "logical_date",
        "related_model",
    )
