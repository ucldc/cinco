import botocore
from django.core.management.base import BaseCommand
from django.db.models import Q

from cincoctrl.airflow_client.exceptions import MWAAAPIError
from cincoctrl.airflow_client.models import JobRun
from cincoctrl.airflow_client.models import JobTrigger
from cincoctrl.airflow_client.mwaa_api_client import update_job_run


class Command(BaseCommand):
    help = "Poll Airflow API for Dag Run Status Changes."

    def handle(self, *args, **kwargs):
        triggers = (
            JobTrigger.objects.filter(dag_run_id__isnull=False).exclude(
                Q(jobrun__status=JobRun.SUCCEEDED) | Q(jobrun__status=JobRun.FAILED),
            ),
        )
        runs = JobRun.objects.exclude(status=JobRun.SUCCEEDED).exclude(
            status=JobRun.FAILED,
        )

        # When PRESERVE_TRIGGER is False, there shouldn't be any duplicates
        jobs = list(set(triggers) | set(runs))

        self.stdout.write(
            f"Found {triggers.count()} triggered jobs and {runs.count()} "
            f"active job runs. Querying {len(jobs)} jobs.",
        )

        for job in jobs:
            try:
                update_job_run(job)
            except MWAAAPIError as e:
                self.stderr.write(e)
                continue
            except botocore.exceptions.ClientError as e:
                self.stderr.write(e)
                continue
