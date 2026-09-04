# VietDub AI V0.1

Desktop workflow for Chinese video → subtitle OCR → OCR correction → Vietnamese translation → Vietnamese TTS → synchronized audio → MP4/SRT export.

## What is included
- Desktop GUI: `run.py`
- Choose MP4/video from the computer
- Subtitle-region coordinates (normalized 0..1)
- Chinese OCR using PaddleOCR
- OCR cue grouping from sampled frames
- Long-term Proper Name Dictionary
- Project OCR Memory
- Vietnamese translation adapter
- Vietnamese TTS voices
- FFmpeg MP4 rendering and SRT export
- 720p / 1080p / 2K output presets
- Existing core models, correction logic, sync planner and tests

## Windows quick start
**Recommended: Python 3.11 x64.** Some AI packages do not yet support every newer Python version.

1. Install Python 3.11 x64.
2. Install FFmpeg and make sure `ffmpeg` and `ffprobe` are available in PATH.
3. Download this repository ZIP and extract it.
4. Double-click `install_windows.bat` once.
5. Double-click `run_windows.bat` to open VietDub.

Or from a terminal:
```bat
install_windows.bat
run_windows.bat
```

## GUI workflow
1. **Chọn video MP4**.
2. Enter subtitle region as X/Y/W/H percentages. Defaults are bottom subtitles.
3. **Chạy OCR**. The program samples frames and groups consecutive identical text into subtitle cues.
4. Review/edit OCR and translate.
5. Create Vietnamese TTS.
6. Render `*_VietDub.mp4` and export SRT next to it.

## Important
- FFmpeg is required for frame extraction and final rendering.
- PaddleOCR downloads/loads its model on first OCR use and can require significant disk/RAM.
- Translation and Edge TTS require network access in this V0.1 implementation.
- For a 3-hour video, use a smaller OCR sampling FPS (for example 0.5–1 FPS) and allow time for processing.
- Do not delete the original video while processing.

## Dictionaries
- `data/dictionaries/proper_names.json` = long-term proper-name dictionary.
- `data/ocr_memory.json` = temporary OCR memory.
- OCR corrections should be deliberately promoted to the long-term dictionary; they are not supposed to become permanent automatically.

## Tests
```bash
python -m pytest -q
```
