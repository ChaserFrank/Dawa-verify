import datetime

from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .extraction import ExtractionFailed, ExtractionNotConfigured, get_extractor
from .models import InventoryItem, VerificationImage, VerificationRequest
from .rules import evaluate
from .serializers import (
    ConfirmInventorySerializer,
    InventoryItemSerializer,
    VerificationResultSerializer,
)
from .speech import (
    SpeechNotConfigured,
    SpeechSynthesisFailed,
    TranslationFailed,
    synthesize_swahili_speech,
    translate_to_swahili,
)


class VerifyMedicineView(APIView):
    """POST /api/verifications/

    Accepts one or more photos (multipart field name "images"), runs
    extraction (real Qwen Vision once configured, stub until then) and
    deterministic rules, and stores + returns the result.
    """

    def post(self, request):
        images = request.FILES.getlist("images")
        if not images:
            return Response(
                {"detail": "At least one image is required (field name: images)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            extractor = get_extractor()
        except ExtractionNotConfigured as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        verification_request = VerificationRequest.objects.create(
            extracted_data={}, extractor_name=extractor.name, result_category=VerificationRequest.CATEGORY_UNVERIFIABLE
        )
        saved_paths = []
        for image in images:
            vi = VerificationImage.objects.create(verification_request=verification_request, image=image)
            saved_paths.append(vi.image.path)

        try:
            extraction = extractor.extract(saved_paths)
        except ExtractionFailed as exc:
            # A real API/parsing failure is NOT the same thing as "could not
            # verify" -- that category means "we read the package but
            # couldn't confirm it". Surface this as a distinct error so a
            # broken Qwen call is never silently shown as a calm result.
            verification_request.evidence = [f"Extraction request failed: {exc}"]
            verification_request.save()
            return Response(
                {
                    "detail": "The extraction service failed to process these images.",
                    "verification_id": str(verification_request.id),
                    "error": str(exc),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        outcome = evaluate(extraction)

        verification_request.extracted_data = extraction.as_dict()
        verification_request.result_category = outcome.category
        verification_request.evidence = outcome.evidence
        verification_request.matched_product = outcome.matched_product
        verification_request.save()

        serializer = VerificationResultSerializer(verification_request, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SpeakSwahiliView(APIView):
    """POST /api/verifications/<id>/speak/

    Translates this verification's printed_instructions to Swahili and
    synthesizes audio, caching both on the VerificationRequest. Returns
    400 if there is nothing printed to explain -- never fabricates
    instructions that weren't on the package.
    """

    def post(self, request, verification_id):
        try:
            verification_request = VerificationRequest.objects.get(id=verification_id)
        except VerificationRequest.DoesNotExist:
            return Response({"detail": "Verification not found."}, status=status.HTTP_404_NOT_FOUND)

        if verification_request.swahili_audio:
            serializer = VerificationResultSerializer(verification_request, context={"request": request})
            return Response(serializer.data)

        instructions = (verification_request.extracted_data or {}).get("printed_instructions")
        if not instructions:
            return Response(
                {"detail": "No printed instructions were extracted from this package to explain."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            swahili_text = translate_to_swahili(instructions)
            audio = synthesize_swahili_speech(swahili_text)
        except (TranslationFailed, SpeechSynthesisFailed, SpeechNotConfigured) as exc:
            return Response(
                {"detail": "Could not generate the Swahili explanation.", "error": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY if not isinstance(exc, SpeechNotConfigured) else status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        verification_request.swahili_text = swahili_text
        verification_request.swahili_audio.save(
            f"{verification_request.id}.mp3", ContentFile(audio.content), save=True
        )

        serializer = VerificationResultSerializer(verification_request, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InventoryListCreateView(APIView):
    """GET /api/inventory/            -> list, newest first
    GET /api/inventory/?expires_within=60  -> filter to items in that window
    POST /api/inventory/              -> confirm extracted/edited data into stock
    """

    def get(self, request):
        queryset = InventoryItem.objects.select_related("batch", "batch__product").order_by(
            "batch__expiry_date"
        )
        expires_within_param = request.query_params.get("expires_within")
        if expires_within_param is not None:
            try:
                days = int(expires_within_param)
            except ValueError:
                return Response(
                    {"detail": "expires_within must be an integer number of days."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            today = datetime.date.today()
            cutoff = today + datetime.timedelta(days=days)
            queryset = queryset.filter(batch__expiry_date__gte=today, batch__expiry_date__lte=cutoff)

        serializer = InventoryItemSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ConfirmInventorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(InventoryItemSerializer(item).data, status=status.HTTP_201_CREATED)
