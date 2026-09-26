from django.contrib import admin

from .models import (
    Batch,
    InventoryItem,
    Product,
    ProductReference,
    VerificationImage,
    VerificationRequest,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "strength", "manufacturer", "dosage_form")
    search_fields = ("name", "manufacturer")


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("product", "batch_number", "expiry_raw_text", "expiry_date", "expiry_precision")
    list_filter = ("expiry_precision",)
    search_fields = ("batch_number", "product__name")


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("batch", "quantity", "location", "updated_at")


@admin.register(ProductReference)
class ProductReferenceAdmin(admin.ModelAdmin):
    # source_description is required in the admin form too: every reference
    # must document where it came from (proposal section 15).
    list_display = ("product", "source_description")


class VerificationImageInline(admin.TabularInline):
    model = VerificationImage
    extra = 0


@admin.register(VerificationRequest)
class VerificationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "result_category", "extractor_name", "created_at", "matched_product")
    list_filter = ("result_category", "extractor_name")
    inlines = [VerificationImageInline]
    readonly_fields = ("id", "created_at", "extracted_data", "evidence")
