import json

from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver

from cincoctrl.airflow_client.models import JobRun
from cincoctrl.airflow_client.mwaa_api_client import trigger_dag
from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordCreator
from cincoctrl.findingaids.models import ExpressRecordSubject
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import IndexingHistory
from cincoctrl.findingaids.models import SupplementaryFile
from cincoctrl.findingaids.models import ValidationWarning
from cincoctrl.findingaids.parser import EADParser


@receiver(post_save, sender=FindingAid)
def update_ead_warnings(sender, instance, created, **kwargs):
    if instance.ead_file.name:
        p = EADParser()
        with instance.ead_file.open("rb") as f:
            p.parse_file(f)
        p.validate_dtd()
        p.validate_dates()
        warn_ids = []
        for w in p.warnings:
            warn, _ = ValidationWarning.objects.get_or_create(
                finding_aid=instance,
                message=w[:255],
            )
            warn_ids.append(warn.pk)
        # Delete any no-longer-relevant warnings
        instance.validationwarning_set.exclude(pk__in=warn_ids).delete()


@receiver(post_save)
def start_indexing_job(sender, instance, created, **kwargs):
    if sender == FindingAid and settings.ENABLE_AIRFLOW:
        ark_name = instance.ark.replace("/", ":")
        trigger_dag(
            "index_finding_aid",
            {
                "finding_aid_id": instance.id,
                "repository_code": instance.repository.code,
                "finding_aid_ark": instance.ark,
                "preview": instance.status != "published",
            },
            related_model=instance,
            dag_run_prefix=f"{settings.AIRFLOW_PROJECT_NAME}__{ark_name}",
        )
    if sender in [ExpressRecord, SupplementaryFile]:
        finding_aid = instance.finding_aid
        post_save.send(sender=FindingAid, instance=finding_aid, created=created)
    if sender in [ExpressRecordCreator, ExpressRecordSubject]:
        finding_aid = instance.record.finding_aid
        post_save.send(sender=FindingAid, instance=finding_aid, created=created)


@receiver(pre_save, sender=SupplementaryFile)
def pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous_instance = SupplementaryFile.objects.get(pk=instance.pk)
        # reset textract status and textract output if pdf_file changes
        if previous_instance.pdf_file != instance.pdf_file:
            instance.textract_status = "IN_PROGRESS"
            instance.textract_output = ""


@receiver(post_save, sender=JobRun)
def update_status(sender, instance, created, **kwargs):
    if instance.status == "succeeded":
        f = instance.related_model
        # dag_run_conf attached on JobRun is kind of wonky
        # the one in JobTrigger seems more reliable
        # not sure why they both have this field
        dag_conf = json.loads(instance.job_trigger.dag_run_conf)
        IndexingHistory.objects.create(finding_aid=f, status="success")
        f.status = "previewed" if dag_conf["preview"] else "published"
        f.save()
    elif instance.status == "failed":
        IndexingHistory.objects.create(
            finding_aid=instance.related_model,
            status="failed",
        )
