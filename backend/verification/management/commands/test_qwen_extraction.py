"""
Standalone manual test for the real Qwen Vision credentials.

Run this yourself against your real .env before trusting the extractor for
a demo -- it was written and unit-tested here, but never called against
the live API (this development environment's network cannot reach
modelscope.ai).

Usage:
    python manage.py test_qwen_extraction path/to/photo.jpg [more photos...]
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from verification.extraction import ExtractionFailed, ExtractionNotConfigured, QwenVisionExtractor


class Command(BaseCommand):
    help = "Send one or more real photos to the configured Qwen Vision model and print the raw result."

    def add_arguments(self, parser):
        parser.add_argument("images", nargs="+", type=str, help="Path(s) to medicine package photo(s)")

    def handle(self, *args, **options):
        if not settings.QWEN_API_KEY or not settings.QWEN_API_BASE or not settings.QWEN_MODEL:
            raise CommandError(
                "QWEN_API_KEY, QWEN_API_BASE and QWEN_MODEL must all be set in your .env first."
            )

        self.stdout.write(f"Model:    {settings.QWEN_MODEL}")
        self.stdout.write(f"Base URL: {settings.QWEN_API_BASE}")
        self.stdout.write(f"Images:   {options['images']}")
        self.stdout.write("Calling Qwen Vision... (this makes a real, billed API request)")

        extractor = QwenVisionExtractor(settings.QWEN_API_KEY, settings.QWEN_API_BASE, settings.QWEN_MODEL)

        try:
            result = extractor.extract(options["images"])
        except ExtractionNotConfigured as exc:
            raise CommandError(str(exc))
        except ExtractionFailed as exc:
            self.stderr.write(self.style.ERROR(f"Extraction failed: {exc}"))
            self.stderr.write(
                self.style.WARNING(
                    "If this says the model doesn't support image input, the model name "
                    "in QWEN_MODEL likely isn't vision-capable -- ask the organizers for a "
                    "'-VL-' model (e.g. something like Qwen3-VL-...) under the same credits."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS("Extraction succeeded:"))
        self.stdout.write(json.dumps(result.as_dict(), indent=2, default=str))
