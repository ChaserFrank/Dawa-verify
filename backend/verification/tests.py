"""
Tests for the deterministic rules (ADR 0003, ADR 0004) and the API
contract the frontend depends on. Run against the real Postgres test
database Django creates for this run (see settings.py) -- not mocked out.
"""
import datetime
import json

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .extraction import ExtractionFailed, ExtractionResult, StubExtractor
from .models import Batch, InventoryItem, Product, VerificationRequest
from .rules import UnparseableExpiry, evaluate, expires_within, is_expired, parse_expiry


class ParseExpiryTests(TestCase):
    def test_month_year_slash_format(self):
        precision, date = parse_expiry("08/2027")
        self.assertEqual(precision, Batch.PRECISION_MONTH)
        self.assertEqual(date, datetime.date(2027, 8, 31))

    def test_month_year_resolves_to_last_day_of_month(self):
        # February, non-leap year
        precision, date = parse_expiry("02/2027")
        self.assertEqual(date, datetime.date(2027, 2, 28))
        # February, leap year
        precision, date = parse_expiry("02/2028")
        self.assertEqual(date, datetime.date(2028, 2, 29))

    def test_day_month_year_slash_format(self):
        precision, date = parse_expiry("15/08/2027")
        self.assertEqual(precision, Batch.PRECISION_DAY)
        self.assertEqual(date, datetime.date(2027, 8, 15))

    def test_month_name_year_format(self):
        precision, date = parse_expiry("August 2027")
        self.assertEqual(precision, Batch.PRECISION_MONTH)
        self.assertEqual(date, datetime.date(2027, 8, 31))

    def test_month_abbreviation_year_format(self):
        precision, date = parse_expiry("Nov 2026")
        self.assertEqual(precision, Batch.PRECISION_MONTH)
        self.assertEqual(date, datetime.date(2026, 11, 30))

    def test_invalid_month_raises(self):
        with self.assertRaises(UnparseableExpiry):
            parse_expiry("13/2027")

    def test_garbage_raises(self):
        with self.assertRaises(UnparseableExpiry):
            parse_expiry("not a date")

    def test_empty_raises(self):
        with self.assertRaises(UnparseableExpiry):
            parse_expiry("")


class ExpiryWindowTests(TestCase):
    def test_is_expired_true_for_past_date(self):
        self.assertTrue(is_expired(datetime.date(2020, 1, 1), as_of=datetime.date(2026, 9, 25)))

    def test_is_expired_false_for_future_date(self):
        self.assertFalse(is_expired(datetime.date(2030, 1, 1), as_of=datetime.date(2026, 9, 25)))

    def test_expires_within_boundary_is_inclusive(self):
        as_of = datetime.date(2026, 9, 25)
        exactly_60 = as_of + datetime.timedelta(days=60)
        self.assertTrue(expires_within(exactly_60, days=60, as_of=as_of))

    def test_expires_within_excludes_61_days_out(self):
        as_of = datetime.date(2026, 9, 25)
        beyond = as_of + datetime.timedelta(days=61)
        self.assertFalse(expires_within(beyond, days=60, as_of=as_of))

    def test_proposal_amoxicillin_example_is_not_within_60_days(self):
        """Regression test for the exact scenario flagged in ADR 0003:
        the proposal's demo Amoxicillin batch expires Nov 2026 -> under
        the month-precision convention that is 30 Nov 2026, which is
        MORE than 60 days from 25 Sep 2026. This must stay false unless
        the convention changes -- silently "fixing" it would hide a real
        demo-data problem.
        """
        as_of = datetime.date(2026, 9, 25)
        _, expiry = parse_expiry("11/2026")
        self.assertEqual(expiry, datetime.date(2026, 11, 30))
        self.assertFalse(expires_within(expiry, days=60, as_of=as_of))
        self.assertEqual((expiry - as_of).days, 66)


class EvaluateRulesTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Amoxicillin", manufacturer="Medisource Ltd.", strength="500 mg", dosage_form="capsule"
        )

    def _extraction(self, **overrides):
        base = dict(
            extractor_name="test",
            product_name="Amoxicillin",
            strength="500 mg",
            manufacturer="Medisource Ltd.",
            dosage_form="capsule",
            batch_number="AMX-24081",
            expiry_raw_text="08/2027",
            printed_instructions="Take one capsule three times daily.",
            confidence=0.9,
            raw_response={},
        )
        base.update(overrides)
        return ExtractionResult(**base)

    def test_missing_required_field_is_unverifiable(self):
        outcome = evaluate(self._extraction(batch_number=None))
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_UNVERIFIABLE)
        self.assertTrue(any("batch_number" in e for e in outcome.evidence))

    def test_unparseable_expiry_is_unverifiable(self):
        outcome = evaluate(self._extraction(expiry_raw_text="whenever"))
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_UNVERIFIABLE)

    def test_expired_batch_is_expiry_warning_even_if_catalogue_matches(self):
        outcome = evaluate(
            self._extraction(expiry_raw_text="01/2020"),
            as_of=datetime.date(2026, 9, 25),
        )
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_EXPIRY_WARNING)

    def test_no_catalogue_match_is_unverifiable_not_warning(self):
        outcome = evaluate(self._extraction(product_name="Totally Unknown Drug"))
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_UNVERIFIABLE)

    def test_catalogue_match_and_not_expired_is_verified(self):
        outcome = evaluate(
            self._extraction(expiry_raw_text="08/2030"),
            as_of=datetime.date(2026, 9, 25),
        )
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_VERIFIED)
        self.assertEqual(outcome.matched_product, self.product)

    def test_stub_extraction_is_always_unverifiable(self):
        """The stub extractor returns all-None fields; evaluate() must
        never turn that into anything but 'could not verify'."""
        result = StubExtractor().extract(["/tmp/fake.jpg"])
        outcome = evaluate(result)
        self.assertEqual(outcome.category, VerificationRequest.CATEGORY_UNVERIFIABLE)


class VerifyMedicineAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_no_images_returns_400(self):
        response = self.client.post(reverse("verify-medicine"), data={}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_with_stub_extractor_returns_unverifiable(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        image = SimpleUploadedFile("front.jpg", b"fake-image-bytes", content_type="image/jpeg")
        response = self.client.post(
            reverse("verify-medicine"), data={"images": [image]}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["result_category"], VerificationRequest.CATEGORY_UNVERIFIABLE)
        self.assertEqual(response.data["category_label"], "Could not verify")
        self.assertIn("evidence", response.data)


class InventoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_confirm_creates_product_batch_and_item(self):
        payload = {
            "product_name": "Amoxicillin",
            "manufacturer": "Medisource Ltd.",
            "strength": "500 mg",
            "dosage_form": "capsule",
            "batch_number": "AMX-24081",
            "expiry_raw_text": "08/2027",
            "quantity": 120,
            "location": "Main shelf",
        }
        response = self.client.post(reverse("inventory-list-create"), data=payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(Batch.objects.count(), 1)
        self.assertEqual(InventoryItem.objects.count(), 1)
        self.assertEqual(response.data["status"], "good")

    def test_confirm_rejects_unparseable_expiry(self):
        payload = {
            "product_name": "X", "manufacturer": "Y", "strength": "1 mg",
            "batch_number": "B1", "expiry_raw_text": "sometime next year", "quantity": 1,
        }
        response = self.client.post(reverse("inventory-list-create"), data=payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("expiry_raw_text", response.data)

    def test_duplicate_batch_number_for_same_product_reuses_batch(self):
        payload = {
            "product_name": "Amoxicillin", "manufacturer": "Medisource Ltd.", "strength": "500 mg",
            "batch_number": "AMX-24081", "expiry_raw_text": "08/2027", "quantity": 10,
        }
        self.client.post(reverse("inventory-list-create"), data=payload, format="json")
        payload["quantity"] = 5
        self.client.post(reverse("inventory-list-create"), data=payload, format="json")
        self.assertEqual(Batch.objects.count(), 1)
        self.assertEqual(InventoryItem.objects.count(), 2)

    def test_list_filters_by_expires_within(self):
        Product.objects.create(name="A", manufacturer="M", strength="1mg")
        near = Batch.objects.create(
            product=Product.objects.get(name="A"), batch_number="NEAR",
            expiry_raw_text="10/2026", expiry_precision=Batch.PRECISION_MONTH,
            expiry_date=datetime.date(2026, 10, 31),
        )
        far = Batch.objects.create(
            product=Product.objects.get(name="A"), batch_number="FAR",
            expiry_raw_text="08/2030", expiry_precision=Batch.PRECISION_MONTH,
            expiry_date=datetime.date(2030, 8, 31),
        )
        InventoryItem.objects.create(batch=near, quantity=1)
        InventoryItem.objects.create(batch=far, quantity=1)

        response = self.client.get(reverse("inventory-list-create"), {"expires_within": 60})
        batch_numbers = [row["batch_number"] for row in response.data]
        self.assertIn("NEAR", batch_numbers)
        self.assertNotIn("FAR", batch_numbers)


class QwenVisionExtractorTests(TestCase):
    """These mock the OpenAI client entirely -- this environment's network
    cannot reach modelscope.ai. They verify our request construction and
    response parsing are correct; they do NOT prove the real API behaves
    as assumed. Run `manage.py test_qwen_extraction` against real
    credentials to verify that.
    """

    def _make_extractor_with_fake_client(self, fake_response_text):
        from unittest.mock import MagicMock

        from .extraction import QwenVisionExtractor

        extractor = QwenVisionExtractor.__new__(QwenVisionExtractor)
        extractor.model = "test-model"
        fake_message = MagicMock(content=fake_response_text)
        fake_choice = MagicMock(message=fake_message)
        fake_response = MagicMock(choices=[fake_choice])
        extractor._client = MagicMock()
        extractor._client.chat.completions.create.return_value = fake_response
        return extractor

    def _tmp_image(self):
        import tempfile
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        f.write(b"fake-bytes")
        f.close()
        return f.name

    def test_parses_clean_json_response(self):
        payload = {
            "product_name": "Amoxicillin", "strength": "500 mg", "manufacturer": "Medisource Ltd.",
            "dosage_form": "capsule", "batch_number": "AMX-24081", "expiry_raw_text": "08/2027",
            "printed_instructions": "Take one capsule three times daily.", "confidence": 0.87,
        }
        extractor = self._make_extractor_with_fake_client(json.dumps(payload))
        result = extractor.extract([self._tmp_image()])
        self.assertEqual(result.product_name, "Amoxicillin")
        self.assertEqual(result.confidence, 0.87)
        self.assertEqual(result.extractor_name, "qwen-vision")

    def test_strips_markdown_json_fence(self):
        payload = {
            "product_name": "X", "strength": "1mg", "manufacturer": "Y", "dosage_form": "tablet",
            "batch_number": "B1", "expiry_raw_text": "01/2028", "printed_instructions": None,
            "confidence": 0.5,
        }
        fenced = "```json\n" + json.dumps(payload) + "\n```"
        extractor = self._make_extractor_with_fake_client(fenced)
        result = extractor.extract([self._tmp_image()])
        self.assertEqual(result.product_name, "X")

    def test_missing_keys_raises_extraction_failed(self):
        extractor = self._make_extractor_with_fake_client(json.dumps({"product_name": "X"}))
        with self.assertRaises(ExtractionFailed):
            extractor.extract([self._tmp_image()])

    def test_invalid_json_raises_extraction_failed(self):
        extractor = self._make_extractor_with_fake_client("not json at all")
        with self.assertRaises(ExtractionFailed):
            extractor.extract([self._tmp_image()])

    def test_no_choices_raises_extraction_failed(self):
        from unittest.mock import MagicMock

        from .extraction import QwenVisionExtractor

        extractor = QwenVisionExtractor.__new__(QwenVisionExtractor)
        extractor.model = "test-model"
        extractor._client = MagicMock()
        extractor._client.chat.completions.create.return_value = MagicMock(choices=[])
        with self.assertRaises(ExtractionFailed):
            extractor.extract([self._tmp_image()])

    def test_transport_error_raises_extraction_failed(self):
        from unittest.mock import MagicMock

        from .extraction import QwenVisionExtractor

        extractor = QwenVisionExtractor.__new__(QwenVisionExtractor)
        extractor.model = "test-model"
        extractor._client = MagicMock()
        extractor._client.chat.completions.create.side_effect = ConnectionError("boom")
        with self.assertRaises(ExtractionFailed):
            extractor.extract([self._tmp_image()])

    def test_missing_credentials_raises_not_configured(self):
        from .extraction import ExtractionNotConfigured, QwenVisionExtractor
        with self.assertRaises(ExtractionNotConfigured):
            QwenVisionExtractor(api_key="", api_base="", model="")


class VerifyMedicineViewFailureTests(TestCase):
    """Confirms an extraction failure surfaces as a distinct 502, never
    disguised as a calm 'could not verify' result."""

    def test_extraction_failure_returns_502(self):
        from unittest.mock import patch
        from django.core.files.uploadedfile import SimpleUploadedFile

        from .extraction import ExtractionFailed

        client = APIClient()
        image = SimpleUploadedFile("front.jpg", b"fake-image-bytes", content_type="image/jpeg")

        with patch("verification.views.get_extractor") as mock_get_extractor:
            mock_extractor = mock_get_extractor.return_value
            mock_extractor.name = "qwen-vision"
            mock_extractor.extract.side_effect = ExtractionFailed("simulated failure")

            response = client.post(reverse("verify-medicine"), data={"images": [image]}, format="multipart")

        self.assertEqual(response.status_code, 502)
        self.assertIn("verification_id", response.data)


class SwahiliSpeechServiceTests(TestCase):
    """Mocked -- this environment can't reach the real Qwen or Azure
    endpoints. These prove our request/response handling and caching
    logic are correct, not that the live services behave as assumed.
    Run manage.py test_swahili_speech against real credentials to verify that.
    """

    def test_translate_returns_stripped_text(self):
        from unittest.mock import MagicMock, patch

        from .speech import translate_to_swahili

        with patch("verification.speech.settings") as mock_settings:
            mock_settings.QWEN_API_KEY = "k"
            mock_settings.QWEN_API_BASE = "b"
            mock_settings.QWEN_MODEL = "m"
            with patch("openai.OpenAI") as MockOpenAI:
                fake_message = MagicMock(content="  Meza kidonge kimoja mara mbili kwa siku.  ")
                fake_choice = MagicMock(message=fake_message)
                MockOpenAI.return_value.chat.completions.create.return_value = MagicMock(choices=[fake_choice])
                result = translate_to_swahili("Take one tablet twice daily.")
        self.assertEqual(result, "Meza kidonge kimoja mara mbili kwa siku.")

    def test_translate_empty_response_raises(self):
        from unittest.mock import MagicMock, patch

        from .speech import TranslationFailed, translate_to_swahili

        with patch("verification.speech.settings") as mock_settings:
            mock_settings.QWEN_API_KEY = "k"
            mock_settings.QWEN_API_BASE = "b"
            mock_settings.QWEN_MODEL = "m"
            with patch("openai.OpenAI") as MockOpenAI:
                MockOpenAI.return_value.chat.completions.create.return_value = MagicMock(choices=[])
                with self.assertRaises(TranslationFailed):
                    translate_to_swahili("Take one tablet.")

    def test_synthesize_missing_config_raises(self):
        from unittest.mock import patch

        from .speech import SpeechNotConfigured, synthesize_swahili_speech

        with patch("verification.speech.settings") as mock_settings:
            mock_settings.AZURE_SPEECH_KEY = ""
            mock_settings.AZURE_SPEECH_REGION = ""
            with self.assertRaises(SpeechNotConfigured):
                synthesize_swahili_speech("habari")

    def test_synthesize_success_returns_audio_bytes(self):
        from unittest.mock import MagicMock, patch

        from .speech import synthesize_swahili_speech

        with patch("verification.speech.settings") as mock_settings:
            mock_settings.AZURE_SPEECH_KEY = "k"
            mock_settings.AZURE_SPEECH_REGION = "eastus"
            mock_settings.AZURE_SPEECH_VOICE = "sw-KE-RafikiNeural"
            fake_response = MagicMock(status_code=200, content=b"fake-mp3-bytes")
            with patch("verification.speech.requests.post", return_value=fake_response) as mock_post:
                result = synthesize_swahili_speech("Habari, meza kidonge kimoja.")
        self.assertEqual(result.content, b"fake-mp3-bytes")
        self.assertEqual(result.content_type, "audio/mpeg")
        call_kwargs = mock_post.call_args.kwargs
        self.assertIn("sw-KE-RafikiNeural", call_kwargs["data"].decode())

    def test_synthesize_non_200_raises(self):
        from unittest.mock import MagicMock, patch

        from .speech import SpeechSynthesisFailed, synthesize_swahili_speech

        with patch("verification.speech.settings") as mock_settings:
            mock_settings.AZURE_SPEECH_KEY = "k"
            mock_settings.AZURE_SPEECH_REGION = "eastus"
            mock_settings.AZURE_SPEECH_VOICE = "sw-KE-RafikiNeural"
            fake_response = MagicMock(status_code=401, text="Unauthorized")
            with patch("verification.speech.requests.post", return_value=fake_response):
                with self.assertRaises(SpeechSynthesisFailed):
                    synthesize_swahili_speech("habari")


class SpeakSwahiliViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _create_verification(self, printed_instructions="Take one tablet twice daily."):
        return VerificationRequest.objects.create(
            extracted_data={
                "product_name": "X", "strength": "1mg", "manufacturer": "Y", "dosage_form": "tablet",
                "batch_number": "B1", "expiry_raw_text": "08/2027",
                "printed_instructions": printed_instructions, "confidence": 0.9,
            },
            extractor_name="test",
            result_category=VerificationRequest.CATEGORY_VERIFIED,
        )

    def test_404_for_unknown_id(self):
        import uuid
        response = self.client.post(reverse("speak-swahili", args=[uuid.uuid4()]))
        self.assertEqual(response.status_code, 404)

    def test_400_when_no_printed_instructions(self):
        vr = self._create_verification(printed_instructions=None)
        response = self.client.post(reverse("speak-swahili", args=[vr.id]))
        self.assertEqual(response.status_code, 400)

    def test_success_caches_on_model(self):
        from unittest.mock import patch

        from .speech import SynthesizedAudio

        vr = self._create_verification()
        with patch("verification.views.translate_to_swahili", return_value="Meza kidonge kimoja."):
            with patch(
                "verification.views.synthesize_swahili_speech",
                return_value=SynthesizedAudio(content=b"fake-mp3", content_type="audio/mpeg"),
            ):
                response = self.client.post(reverse("speak-swahili", args=[vr.id]))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["swahili_text"], "Meza kidonge kimoja.")
        self.assertIsNotNone(response.data["swahili_audio_url"])
        vr.refresh_from_db()
        self.assertTrue(vr.swahili_audio.name)

    def test_second_call_reuses_cache_without_recalling_services(self):
        from unittest.mock import patch

        from django.core.files.base import ContentFile

        vr = self._create_verification()
        vr.swahili_text = "Tayari imetafsiriwa."
        vr.swahili_audio.save("cached.mp3", ContentFile(b"cached-bytes"), save=True)

        with patch("verification.views.translate_to_swahili") as mock_translate:
            response = self.client.post(reverse("speak-swahili", args=[vr.id]))
        mock_translate.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["swahili_text"], "Tayari imetafsiriwa.")

    def test_translation_failure_returns_502(self):
        from unittest.mock import patch

        from .speech import TranslationFailed

        vr = self._create_verification()
        with patch("verification.views.translate_to_swahili", side_effect=TranslationFailed("boom")):
            response = self.client.post(reverse("speak-swahili", args=[vr.id]))
        self.assertEqual(response.status_code, 502)

    def test_not_configured_returns_503(self):
        from unittest.mock import patch

        from .speech import SpeechNotConfigured

        vr = self._create_verification()
        with patch("verification.views.translate_to_swahili", side_effect=SpeechNotConfigured("no key")):
            response = self.client.post(reverse("speak-swahili", args=[vr.id]))
        self.assertEqual(response.status_code, 503)
