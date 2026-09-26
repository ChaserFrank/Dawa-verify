"""
Data model for Dawa Verify.

Follows the proposal's section 10 model (Product, Batch, InventoryItem,
VerificationRequest, ProductReference), with two corrections recorded in
the ADRs and applied here rather than left implicit:

- ADR 0002: a batch number is only unique per product, not globally, so
  the uniqueness constraint is (product, batch_number).
- ADR 0003: a month/year-only expiry is stored as the raw printed text
  AND as a computed date valid through the last day of that month. Rules
  and queries use the computed date; the raw text is kept for display so
  extracted text and interpretation stay visibly separate (ADR 0004).
"""
import calendar
import uuid

from django.core.exceptions import ValidationError
from django.db import models


class Product(models.Model):
    """A medicine identity: name + strength + manufacturer + dosage form.

    Distinct strengths or manufacturers of the "same" medicine name are
    different Products, because verification depends on all four fields
    matching, not just the name.
    """

    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    strength = models.CharField(max_length=100, help_text="e.g. '500 mg'")
    dosage_form = models.CharField(
        max_length=100, blank=True, help_text="e.g. 'tablet', 'capsule', 'syrup'"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "manufacturer", "strength", "dosage_form"],
                name="unique_product_identity",
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} {self.strength} ({self.manufacturer})"


def _last_day_of_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return year, month, last_day


class Batch(models.Model):
    """A specific production batch of a Product.

    expiry_precision records what was actually printed on the package, so
    the raw text is never silently discarded, and expiry_date is always the
    date used for comparisons (ADR 0003):
      - "day": the printed date is used as-is.
      - "month": expiry_date is set to the last day of the printed month.
    """

    PRECISION_DAY = "day"
    PRECISION_MONTH = "month"
    PRECISION_CHOICES = [
        (PRECISION_DAY, "Exact day printed"),
        (PRECISION_MONTH, "Month and year only"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="batches")
    batch_number = models.CharField(max_length=100)
    manufacturing_date = models.DateField(null=True, blank=True)

    expiry_raw_text = models.CharField(
        max_length=50, help_text="Expiry exactly as printed on the package, e.g. '08/2027'"
    )
    expiry_precision = models.CharField(max_length=10, choices=PRECISION_CHOICES)
    expiry_date = models.DateField(help_text="Computed per ADR 0003; used for all comparisons")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "batch_number"], name="unique_batch_per_product"
            )
        ]
        ordering = ["expiry_date"]

    def __str__(self):
        return f"{self.product} — batch {self.batch_number}"

    def clean(self):
        if self.expiry_precision == self.PRECISION_MONTH and self.expiry_date:
            year, month, day = self.expiry_date.year, self.expiry_date.month, self.expiry_date.day
            _, _, last_day = _last_day_of_month(year, month)
            if day != last_day:
                raise ValidationError(
                    "Month-precision expiry_date must be set to the last day of that month "
                    f"({year}-{month:02d}-{last_day:02d}), per ADR 0003."
                )

    @classmethod
    def compute_expiry_date(cls, year, month, day=None):
        """Apply ADR 0003: month-only expiry resolves to the last day of that month."""
        if day is not None:
            precision = cls.PRECISION_DAY
        else:
            precision = cls.PRECISION_MONTH
            year, month, day = _last_day_of_month(year, month)
        import datetime

        return precision, datetime.date(year, month, day)


class InventoryItem(models.Model):
    """A pharmacy's on-hand quantity of a specific Batch at a location."""

    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="inventory_items")
    quantity = models.PositiveIntegerField()
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.batch}"


class ProductReference(models.Model):
    """A trusted reference record for a product, used for catalogue matching.

    source_description is required (not blank) per the proposal section 15:
    every reference must document where it came from.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="references"
    )
    source_description = models.TextField(
        help_text="Where this reference came from, e.g. 'Manufacturer packaging insert, photographed 2026-09-20'"
    )
    reference_image = models.ImageField(upload_to="reference_images/", null=True, blank=True)

    def __str__(self):
        return f"Reference for {self.product}"


class VerificationRequest(models.Model):
    """One user-submitted verification attempt: the images, what was
    extracted from them, and the resulting verification outcome.

    extracted_data and ai_explanation are stored separately from each
    other and from the deterministic result fields, per ADR 0004: the
    system must be able to show what was read vs. what was interpreted
    vs. what was ruled on, as three distinct things.
    """

    CATEGORY_VERIFIED = "verified"
    CATEGORY_WARNING = "warning"
    CATEGORY_UNVERIFIABLE = "unverifiable"
    CATEGORY_EXPIRY_WARNING = "expiry_warning"
    CATEGORY_CHOICES = [
        (CATEGORY_VERIFIED, "Information verified"),
        (CATEGORY_WARNING, "Potential warning signs"),
        (CATEGORY_UNVERIFIABLE, "Could not verify"),
        (CATEGORY_EXPIRY_WARNING, "Expiry warning"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # What the extractor returned, verbatim (JSON). Never edited after the
    # fact -- this is "what was read", per ADR 0004.
    extracted_data = models.JSONField()
    extractor_name = models.CharField(
        max_length=100, help_text="Which extractor produced extracted_data, e.g. 'qwen-vision' or 'stub-v1'"
    )

    result_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    evidence = models.JSONField(
        default=list, help_text="List of short evidence strings backing result_category"
    )

    matched_product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL, related_name="verification_requests"
    )
    confirmed_batch = models.ForeignKey(
        Batch, null=True, blank=True, on_delete=models.SET_NULL, related_name="verification_requests"
    )

    # Swahili explanation cache (ADR 0006). Populated on first successful
    # call to /speak/, reused after that -- never regenerated silently on
    # every request, since translation + synthesis are both billed calls.
    swahili_text = models.TextField(
        blank=True, default="", help_text="Qwen translation of extracted_data.printed_instructions"
    )
    swahili_audio = models.FileField(upload_to="verification_audio/", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"VerificationRequest {self.id} ({self.result_category})"


def verification_image_upload_path(instance, filename):
    return f"verification_requests/{instance.verification_request_id}/{filename}"


class VerificationImage(models.Model):
    """One uploaded photo belonging to a VerificationRequest."""

    verification_request = models.ForeignKey(
        VerificationRequest, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to=verification_image_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
