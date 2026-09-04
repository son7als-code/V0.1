from __future__ import annotations
import asyncio
from pathlib import Path

async def _make(text: str, out: str, voice: str):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(out)


def synthesize(text: str, out: str, voice: str = 'vi-VN-HoaiMyNeural') -> str:
    if not text: raise ValueError('TTS text is empty')
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    try:
        asyncio.run(_make(text, out, voice))
    except Exception as e:
        raise RuntimeError(f'TTS thất bại: {e}') from e
    return out
