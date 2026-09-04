# VietDub Core V0.1

Core backend for Chinese video -> OCR -> correction -> Vietnamese translation -> TTS -> sync -> render.

## V0.1 scope
- Project state and subtitle cues
- Normalized subtitle-region coordinates
- Long-term Proper Name Dictionary
- Per-project OCR Memory
- OCR correction with project memory priority
- Translation/TTS adapters
- Dialogue synchronization planner
- Pipeline orchestration
- Unit tests

AI/media providers are adapters so real OCR, Whisper, translation, TTS and FFmpeg can be plugged in later.

## Run
```bash
python -m pytest -q
python -m app.demo
```

## Dictionary design
`data/dictionaries/proper_names.json` is long-term.
`data/projects/<project_id>/ocr_memory.json` is temporary/project-local.
OCR corrections are never promoted automatically.