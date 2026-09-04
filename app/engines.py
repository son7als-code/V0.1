from pathlib import Path
from typing import Protocol

class OCRProvider(Protocol):
    def recognize(self, video_path, region, start, end): ...
class TranslationProvider(Protocol):
    def translate(self, text, context=None): ...
class TTSProvider(Protocol):
    def synthesize(self, text, voice, output_path): ...
class MediaProvider(Protocol):
    def extract_audio(self, video_path, output_path): ...
    def render(self, video_path, audio_path, output_path, resolution): ...

class MockTranslator:
    def translate(self, text, context=None): return '[VI] ' + text

class MockTTS:
    def synthesize(self, text, voice, output_path):
        p=Path(output_path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f'VOICE={voice}\nTEXT={text}\n', encoding='utf-8')
        return str(p)