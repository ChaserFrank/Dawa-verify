from rest_framework import serializers

from .models import Batch, InventoryItem, Product, VerificationRequest

# Category machine-values -> the exact label strings app.js/index.html
# already render (status pills, history items), so the frontend swap is a
# straight field read, not a redesign.
CATEGORY_LABELS = {
    VerificationRequest.CATEGORY_VERIFIED: "Information verified",
    VerificationRequest.CATEGORY_WARNING: "Potential warning signs",
    VerificationRequest.CATEGORY_UNVERIFIABLE: "Could not verify",
    VerificationRequest.CATEGORY_EXPIRY_WARNING: "Expiry warning",
}


class VerificationResultSerializer(serializers.ModelSerializer):
    """Shape returned by POST /api/verifications/. Matches the fields the
    result view in index.html needs: product name/strength, category label,
    evidence list, and enough of the matched product to prefill a
    save-to-inventory confirmation.
    """

    category_label = serializers.SerializerMethodField()
    product_name = serializers.SerializerMethodField()
    strength = serializers.SerializerMethodField()
    manufacturer = serializers.SerializerMethodField()
    extracted = serializers.JSONField(source="extracted_data")
    swahili_audio_url = serializers.SerializerMethodField()

    class Meta:
        model = VerificationRequest
        fields = [
            "id",
            "result_category",
            "category_label",
            "evidence",
            "extracted",
            "product_name",
            "strength",
            "manufacturer",
            "created_at",
            "swahili_text",
            "swahili_audio_url",
        ]

    def get_swahili_audio_url(self, obj):
        if not obj.swahili_audio:
            return None
        request = self.context.get("request")
        url = obj.swahili_audio.url
        return request.build_absolute_uri(url) if request else url

    def get_category_label(self, obj):
        return CATEGORY_LABELS.get(obj.result_category, obj.result_category)

    def get_product_name(self, obj):
        return obj.matched_product.name if obj.matched_product else obj.extracted_data.get("product_name")

    def get_strength(self, obj):
        return obj.matched_product.strength if obj.matched_product else obj.extracted_data.get("strength")

    def get_manufacturer(self, obj):
        return obj.matched_product.manufacturer if obj.matched_product else obj.extracted_data.get("manufacturer")


class InventoryItemSerializer(serializers.ModelSerializer):
    """Shape matching the inventory table columns in index.html:
    Medicine / Batch / Expiry / Quantity / Status.
    """

    medicine = serializers.CharField(source="batch.product.name", read_only=True)
    manufacturer = serializers.CharField(source="batch.product.manufacturer", read_only=True)
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True)
    expiry_raw_text = serializers.CharField(source="batch.expiry_raw_text", read_only=True)
    expiry_date = serializers.DateField(source="batch.expiry_date", read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "medicine",
            "manufacturer",
            "batch_number",
            "expiry_raw_text",
            "expiry_date",
            "quantity",
            "location",
            "status",
        ]

    def get_status(self, obj):
        from .rules import expires_within, is_expired

        expiry_date = obj.batch.expiry_date
        if is_expired(expiry_date):
            return "expired"
        if expires_within(expiry_date, days=60):
            return "within_60_days"
        return "good"


class ConfirmInventorySerializer(serializers.Serializer):
    """Input for POST /api/inventory/ -- confirming a verification result
    (or manually-entered data) into a stored inventory record. Section 7
    of the proposal: pharmacist reviews extracted info, then confirms.
    """

    verification_id = serializers.UUIDField(required=False, allow_null=True)

    product_name = serializers.CharField()
    manufacturer = serializers.CharField()
    strength = serializers.CharField()
    dosage_form = serializers.CharField(required=False, allow_blank=True, default="")

    batch_number = serializers.CharField()
    expiry_raw_text = serializers.CharField()

    quantity = serializers.IntegerField(min_value=1)
    location = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_expiry_raw_text(self, value):
        from .rules import UnparseableExpiry, parse_expiry

        try:
            parse_expiry(value)
        except UnparseableExpiry as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def create(self, validated_data):
        from .rules import parse_expiry

        product, _ = Product.objects.get_or_create(
            name=validated_data["product_name"],
            manufacturer=validated_data["manufacturer"],
            strength=validated_data["strength"],
            dosage_form=validated_data.get("dosage_form", ""),
        )
        precision, expiry_date = parse_expiry(validated_data["expiry_raw_text"])
        batch, _ = Batch.objects.get_or_create(
            product=product,
            batch_number=validated_data["batch_number"],
            defaults={
                "expiry_raw_text": validated_data["expiry_raw_text"],
                "expiry_precision": precision,
                "expiry_date": expiry_date,
            },
        )
        item = InventoryItem.objects.create(
            batch=batch,
            quantity=validated_data["quantity"],
            location=validated_data.get("location", ""),
        )
        return item
