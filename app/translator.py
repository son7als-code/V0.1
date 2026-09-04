from __future__ import annotations

class VietnameseTranslator:
    def __init__(self):
        self._translator = None

    def translate(self, text: str) -> str:
        if not text: return ''
        try:
            from deep_translator import GoogleTranslator
            if self._translator is None:
                self._translator = GoogleTranslator(source='zh-CN', target='vi')
            return self._translator.translate(text) or text
        except Exception as e:
            raise RuntimeError(f'Dịch tự động thất bại: {e}') from e
