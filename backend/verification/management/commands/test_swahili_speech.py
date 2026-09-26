"""
Standalone manual test for real Qwen translation + Azure Speech synthesis.

This environment's network cannot reach *.tts.speech.microsoft.com, so this
was never called against the live API from here. Run it yourself before
the demo.

Usage:
    python manage.py test_swahili_speech "Take one tablet twice daily after meals."
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from verification.speech import (
    SpeechNotConfigured,
    SpeechSynthesisFailed,
    TranslationFailed,
    synthesize_swahili_speech,
    translate_to_swahili,
)


class Command(BaseCommand):
    help = "Translate English instructions to Swahili and synthesize audio, saving the result locally."

    def add_arguments(self, parser):
        parser.add_argument("instructions", type=str, help="English (or source-language) instructions text")
        parser.add_argument("--out", type=str, default="swahili_test_output.mp3")

    def handle(self, *args, **options):
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            raise CommandError("AZURE_SPEECH_KEY and AZURE_SPEECH_REGION must be set in your .env first.")

        self.stdout.write("Translating to Swahili via Qwen...")
        try:
            swahili_text = translate_to_swahili(options["instructions"])
        except TranslationFailed as exc:
            raise CommandError(f"Translation failed: {exc}")
        self.stdout.write(self.style.SUCCESS(f"Swahili: {swahili_text}"))

        self.stdout.write(f"Synthesizing with voice {settings.AZURE_SPEECH_VOICE}...")
        try:
            audio = synthesize_swahili_speech(swahili_text)
        except SpeechNotConfigured as exc:
            raise CommandError(str(exc))
        except SpeechSynthesisFailed as exc:
            self.stderr.write(self.style.ERROR(f"Synthesis failed: {exc}"))
            return

        with open(options["out"], "wb") as fh:
            fh.write(audio.content)
        self.stdout.write(self.style.SUCCESS(f"Saved {len(audio.content)} bytes to {options['out']}"))
