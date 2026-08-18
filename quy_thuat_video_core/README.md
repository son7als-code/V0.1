# Quy Thuat Video AI Core V0.1

A lightweight local project-preparation core for AI-assisted video planning.

V0.1 is CPU-only and does **not** generate images, video, audio, or run local AI models. It prepares project data: story JSON, character profiles, scene plans, and structured image/video prompts.

## Architecture

- `app/main.py` provides a small CLI.
- `app/providers/base.py` defines the replaceable provider interface.
- `app/providers/mock_provider.py` works without API keys or network access.
- `app/providers/external_provider.py` is a clean generic HTTP adapter for a future external AI endpoint.
- `app/core/` contains story orchestration, character reuse, scene normalization, prompt building, and validation.
- `app/storage/` stores each project across small JSON files rather than one huge file.

## What V0.1 intentionally does not include

No Docker, Electron, CUDA, PyTorch, TensorFlow, Stable Diffusion, local LLMs, local video generation, GPU acceleration, or background AI workers.

## Install

Python 3.11+ is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
. .venv/bin/activate
pip install -r requirements.txt
```

`pytest` is only needed for tests. Runtime uses the Python standard library.

## Mock mode

Mock mode requires no API key and creates deterministic dummy project data:

```bash
cd quy_thuat_video_core
python -m app.main --mock
```

Optional inputs:

```bash
cd quy_thuat_video_core
python -m app.main --mock \
  --project-name "Long Thanh Thuc Tinh" \
  --story-title "Long Thanh Thức Tỉnh" \
  --story-topic "A weak young cultivator awakens the bloodline of an ancient dragon." \
  --language Vietnamese \
  --target-duration "5 minutes" \
  --genre "Xianxia / cultivation" \
  --visual-style "Cinematic Chinese fantasy" \
  --number-of-scenes 20
```

## Retry one failed scene

Retries replace only the requested scene and keep the existing project, characters, and other scenes:

```bash
cd quy_thuat_video_core
python -m app.main --mock --project-dir projects/long_thanh_thuc_tinh --retry-scene scene_005
```

## External provider configuration

Copy `.env.example` and set environment variables in your shell or `.env` loader of choice. API keys are never hard-coded and are not written to project JSON or logs.

```text
AI_API_KEY=
AI_MODEL=
AI_BASE_URL=
```

The generic external adapter posts JSON to:

- `${AI_BASE_URL}/generate_story`
- `${AI_BASE_URL}/generate_scene`

## Project storage layout

```text
projects/project_id/
  project.json
  story.json
  characters.json
  scenes.json
  prompts/scene_001.json
  logs/project.log
```

## Run tests

```bash
pytest
```
