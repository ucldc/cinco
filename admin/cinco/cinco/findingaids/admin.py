from django.contrib import admin

from .models import *

class SupplementaryFileInline(admin.TabularInline):
    model = SupplementaryFile

class FindingAidAdmin(admin.ModelAdmin):
    inlines = [SupplementaryFileInline,]

class ExpressRecordFieldInline(admin.TabularInline):
    model = ExpressRecordField

class ExpressRecordAdmin(admin.ModelAdmin):
    inlines = [ExpressRecordFieldInline,]

admin.site.register(FindingAid, FindingAidAdmin)
admin.site.register(ExpressRecord, ExpressRecordAdmin)