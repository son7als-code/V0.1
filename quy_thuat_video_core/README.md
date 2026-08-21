# Quy Thuat Video AI Core V0.1

A lightweight local project-preparation core for AI-assisted video planning.

V0.1 is CPU-only and does **not** generate images, video, audio, or run local AI models. It prepares project data: story JSON, character profiles, scene plans, and structured image/video prompts.

## Architecture

- `app/main.py` provides a small CLI.
- `app/providers/base.py` defines the replaceable provider interface.
- `app/providers/mock_provider.py` works without API keys or network access.
- `app/providers/external_provider.py` is a clean generic HTTP adapter for a future external AI endpoint.
- `app/core/` contains story orchestration, character reuse, scene normalization, prompt building, validation, and machine-key verification.
- `app/storage/` stores each project across small JSON files rather than one huge file.

## What V0.1 intentionally does not include

No Docker, Electron, CUDA, PyTorch, TensorFlow, Stable Diffusion, local LLMs, local video generation, GPU acceleration, or background AI workers.

## Install

Python 3.11+ is recommended. Runtime uses only the Python standard library; `pytest` is only needed for tests.

### Windows PowerShell

```powershell
cd quy_thuat_video_core
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Windows CMD

```bat
cd quy_thuat_video_core
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

### macOS/Linux

```bash
cd quy_thuat_video_core
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Mock mode

Mock mode requires no API key and creates deterministic dummy project data. PowerShell:

```powershell
cd quy_thuat_video_core
python -m app.main --mock
```

CMD:

```bat
cd quy_thuat_video_core
python -m app.main --mock
```

Optional inputs are shown as a single Windows-friendly command:

```powershell
cd quy_thuat_video_core
python -m app.main --mock --project-name "Long Thanh Thuc Tinh" --story-title "Long Thanh Thức Tỉnh" --story-topic "A weak young cultivator awakens the bloodline of an ancient dragon." --language Vietnamese --target-duration "5 minutes" --genre "Xianxia / cultivation" --visual-style "Cinematic Chinese fantasy" --number-of-scenes 20
```

## Machine key

V0.1 can optionally lock execution to one computer. The machine key is derived from the Windows SMBIOS system UUID using SHA-256; the UUID itself is not stored by the application.

Show the current computer's V0.1 key:

```powershell
cd quy_thuat_video_core
python -m app.main --show-machine-key
```

Enable the machine lock for the current PowerShell session:

```powershell
$env:V01_MACHINE_KEY="V01-PASTE-YOUR-KEY-HERE"
$env:V01_REQUIRE_MACHINE_KEY="true"
python -m app.main --mock
```

For normal development, leave `V01_REQUIRE_MACHINE_KEY=false`. Do not commit a real machine key to Git.

## Retry one failed scene

Retries replace only the requested scene and keep the existing project, characters, and other scenes:

```powershell
cd quy_thuat_video_core
python -m app.main --mock --project-dir projects/long_thanh_thuc_tinh --retry-scene scene_005
```

## External provider configuration

Copy `.env.example` and set environment variables in your shell or `.env` loader of choice. API keys are never hard-coded and are not written to project JSON or logs.

```text
AI_API_KEY=
AI_MODEL=
AI_BASE_URL=
V01_MACHINE_KEY=
V01_REQUIRE_MACHINE_KEY=false
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
