import botocore
from django.core.management.base import BaseCommand

from cincoctrl.airflow_client.exceptions import MWAAAPIError
from cincoctrl.airflow_client.models import JobRun
from cincoctrl.airflow_client.models import JobTrigger
from cincoctrl.airflow_client.mwaa_api_client import update_job_run


class Command(BaseCommand):
    help = "Poll Airflow API for Dag Run Status Changes."

    def handle(self, *args, **kwargs):
        triggered_jobs = JobTrigger.objects.filter(
            dag_run_id__isnull=False,
            jobrun__status=JobRun.RUNNING,
        )
        self.stdout.write(f"Found {triggered_jobs.count()} triggered jobs.")

        for job_trigger in triggered_jobs:
            try:
                update_job_run(job_trigger)
            except MWAAAPIError as e:
                self.stderr.write(e)
                continue
            except botocore.exceptions.ClientError as e:
                self.stderr.write(e)
                continue
