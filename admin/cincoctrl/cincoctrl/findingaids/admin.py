from django.contrib import admin

from cincoctrl.findingaids.models import ExpressRecord
from cincoctrl.findingaids.models import ExpressRecordField
from cincoctrl.findingaids.models import FindingAid
from cincoctrl.findingaids.models import SupplementaryFile


class SupplementaryFileInline(admin.TabularInline):
    model = SupplementaryFile


@admin.register(FindingAid)
class FindingAidAdmin(admin.ModelAdmin):
    inlines = [SupplementaryFileInline]


class ExpressRecordFieldInline(admin.TabularInline):
    model = ExpressRecordField


@admin.register(ExpressRecord)
class ExpressRecordAdmin(admin.ModelAdmin):
    inlines = [ExpressRecordFieldInline]
