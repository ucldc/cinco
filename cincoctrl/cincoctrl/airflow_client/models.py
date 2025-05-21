from urllib.parse import urlencode

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe

if "AIRFLOW_PRESERVE_JOB_TRIGGER" in dir(settings):
    PRESERVE_TRIGGER = settings.AIRFLOW_PRESERVE_JOB_TRIGGER
else:
    PRESERVE_TRIGGER = False


class Job(models.Model):
    related_models = models.ManyToManyField(
        settings.AIRFLOW_JOB_RELATED_MODEL,
    )
    dag_id = models.CharField(max_length=255)
    dag_run_conf = models.TextField(blank=True)
    airflow_url = models.CharField(max_length=255)
    dag_run_id = models.CharField(max_length=255, blank=True)
    logical_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        ordering = ["-logical_date"]

    def __str__(self):
        if self.dag_run_id:
            return f"{self.dag_id}: {self.display_date}"
            # return f"{self.dag_id}: {self.dag_run_id}"
        return "No dag_run_id, check rest api response for details"

    def _key(self):
        return (
            self.dag_run_id,
            self.dag_id,
            self.logical_date,
        )

    def __eq__(self, other):
        if isinstance(other, Job):
            return self._key() == other._key()
        return False

    def __hash__(self):
        return hash(self._key())

    @property
    def dag_run_airflow_url(self):
        query = {"dag_run_id": self.dag_run_id}
        return (
            f"{self.airflow_url}/dags/{self.dag_id}/"
            f"grid?&{urlencode(query)}&base_date="
        )

    @property
    @admin.display(description="Dag Run Logical Date", ordering="logical_date")
    def display_date(self):
        # logical date is in UTC time, display in local timezone
        dt = self.logical_date.astimezone(timezone.get_current_timezone())
        return timezone.datetime.strftime(dt, "%b %d, %Y, %-I:%M:%S %p %Z")

    @property
    @admin.display(description="Dag Run Logical Date", ordering="logical_date")
    def utc_date(self):
        return self.logical_date.strftime("%Y-%m-%d %H:%M:%S %Z")


class JobTrigger(Job):
    """Model to track airflow job triggers"""

    rest_api_status_code = models.TextField(blank=True)
    rest_api_response = models.TextField(blank=True)


def make_status_box(href, text, color):
    box = f"""
        <a href='{href}' target='_blank' alt='{text}'
           style='
               display: inline-block;
               height: 12px; width: 12px;
               border-radius: 2px;
               background-color: {color};'></a>
        """
    return mark_safe(box)  # noqa: S308


class JobRun(Job):
    """Model to track airflow job runs"""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STATUS_CHOICES = (
        (RUNNING, "running"),
        (SUCCEEDED, "succeeded"),
        (FAILED, "failed"),
    )
    # this is a foreign key instead of a 1:1 to allow for a new job run
    # to be created if the job is re-run via airflow's UI without creating
    # a new job trigger. (more a consideration for rikolti than cinco)
    job_trigger = models.ForeignKey(
        JobTrigger,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=255,
        default="running",
        verbose_name="Manually update status",
    )

    @admin.display(description="Status", ordering="status")
    def display_status(self):
        alt_text = "Airflow Dag Run Id"
        color = "lawngreen"
        if self.status == "failed":
            color = "red"
        elif self.status == "succeeded":
            color = "green"
        return make_status_box(self.dag_run_airflow_url, alt_text, color)
