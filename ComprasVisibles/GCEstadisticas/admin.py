from django.contrib import admin

from .models import Entity, EntityType, PurchaseCategory, Requisition, Supplier, Proposal, Awarded

class EntityTypeAdmin(admin.ModelAdmin):
    list_display = ('id','name')

class RequisitionAdmin(admin.ModelAdmin):
    list_display = ['nog']

class PurchaseCategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name']

admin.site.register(EntityType, EntityTypeAdmin)
admin.site.register(Requisition, RequisitionAdmin)
admin.site.register(Proposal)
admin.site.register(Awarded)
admin.site.register(PurchaseCategory, PurchaseCategoryAdmin)
