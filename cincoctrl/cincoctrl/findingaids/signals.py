import boto3
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import post_save
from django.db.models.signals import pre_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver

from cincoctrl.airflow_client.models import JobRun
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
        p.validate_component_titles()
        warn_ids = []
        for w in p.warnings:
            warn, _ = ValidationWarning.objects.get_or_create(
                finding_aid=instance,
                message=w[:255],
            )
            warn_ids.append(warn.pk)
        # Delete any no-longer-relevant warnings
        instance.validationwarning_set.exclude(pk__in=warn_ids).delete()


@receiver(pre_delete, sender=FindingAid)
def delete_s3_ead_file_on_model_delete(sender, instance, **kwargs):
    # instance.ead_file.delete(save=False) tells django-storages to delete
    # the associated S3 object without attempting to save the model instance
    # again - unnecessary during deletion.
    if instance.ead_file:
        instance.ead_file.delete(save=False)


@receiver(pre_delete, sender=SupplementaryFile)
def delete_s3_pdf_file_on_model_delete(sender, instance, **kwargs):
    # instance.pdf_file.delete(save=False) tells django-storages to delete
    # the associated S3 object without attempting to save the model instance
    # again - unnecessary during deletion.
    if instance.pdf_file:
        instance.pdf_file.delete(save=False)
    if instance.textract_output:
        s3 = boto3.resource("s3")
        prefix = f"{instance.textract_output}/"
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        bucket.objects.filter(Prefix=prefix).delete()


@receiver(pre_save, sender=SupplementaryFile)
def pre_save(sender, instance, **kwargs):
    if instance.pk:
        previous_instance = SupplementaryFile.objects.get(pk=instance.pk)
        # reset textract status and textract output if pdf_file changes
        if previous_instance.pdf_file != instance.pdf_file:
            instance.textract_status = "IN_PROGRESS"
            instance.textract_output = ""


@receiver(post_save, sender=SupplementaryFile)
def trigger_reindex(sender, instance, created, **kwargs):
    if instance.textract_status == "SUCCEEDED" and instance.textract_output:
        instance.finding_aid.queue_index()


@receiver(post_save, sender=JobRun)
def update_status(sender, instance, created, **kwargs):
    for related_model in instance.related_models.all():
        current_status = related_model.status
        updated_status = current_status
        if instance.status == "succeeded":
            IndexingHistory.objects.create(
                finding_aid=related_model,
                status="success",
            )
            if current_status == "queued_preview":
                updated_status = "previewed"
            elif current_status == "queued_publish":
                updated_status = "published"
        elif instance.status == "failed":
            IndexingHistory.objects.create(
                finding_aid=related_model,
                status="failed",
            )
            if current_status == "queued_preview":
                updated_status = "preview_error"
            elif current_status == "queued_publish":
                updated_status = "publish_error"

        if current_status != updated_status:
            related_model.status = updated_status
            related_model.save()


@receiver(post_save, sender=JobRun)
def remove_old_job_runs(sender, instance, created, **kwargs):
    for related_model in instance.related_models.all():
        # Find most recent successful job run for the same finding aid
        recent_success = (
            JobRun.objects.filter(
                related_models__id=related_model.id,
                status=JobRun.SUCCEEDED,
            )
            .order_by("-logical_date")
            .first()
        )

        # Remove older job runs for the same finding aid
        JobRun.objects.filter(
            related_models__id=related_model.id,
            logical_date__lt=recent_success.logical_date,
        ).exclude(Q(pk=instance.pk) | Q(pk=recent_success.pk)).delete()
