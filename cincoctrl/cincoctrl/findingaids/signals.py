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
        if instance.status in ("queued_preview", "queued_publish"):
            ark_name = instance.ark.replace("/", ":")
            trigger_dag(
                "index_finding_aid",
                {
                    "finding_aid_id": instance.id,
                    "repository_code": instance.repository.code,
                    "finding_aid_ark": instance.ark,
                    "preview": instance.status == "queued_preview",
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
    current_status = instance.related_model.status
    updated_status = current_status
    if instance.status == "succeeded":
        IndexingHistory.objects.create(
            finding_aid=instance.related_model,
            status="success",
        )
        if current_status == "queued_preview":
            updated_status = "previewed"
        elif current_status == "queued_publish":
            updated_status = "published"
    elif instance.status == "failed":
        IndexingHistory.objects.create(
            finding_aid=instance.related_model,
            status="failed",
        )
        if current_status == "queued_preview":
            updated_status = "preview_error"
        elif current_status == "queued_publish":
            updated_status = "publish_error"

    if current_status != updated_status:
        instance.related_model.save()
