from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _candidate_executables(name: str) -> list[Path]:
    """Return likely FFmpeg executable locations on Windows and other OSes."""
    exe = f"{name}.exe" if os.name == "nt" else name
    candidates: list[Path] = [
        # Normal project layout.
        ROOT / "ffmpeg" / "bin" / exe,
        ROOT / "ffmpeg" / exe,
        ROOT / "bin" / exe,
        ROOT / exe,
    ]

    # Also support a downloaded/extracted FFmpeg folder copied into the project.
    ffmpeg_dir = ROOT / "ffmpeg"
    if ffmpeg_dir.is_dir():
        candidates.extend(ffmpeg_dir.rglob(exe))

    # Support the common case where FFmpeg was downloaded to the Windows Desktop.
    if os.name == "nt":
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if desktop.is_dir():
            candidates.extend(
                [
                    desktop / "ffmpeg" / "bin" / exe,
                    desktop / "ffmpeg" / exe,
                    desktop / exe,
                ]
            )
            # Handles folders such as ffmpeg-8.x-essentials_build\bin\ffmpeg.exe.
            for child in desktop.glob("ffmpeg*"):
                if child.is_dir():
                    candidates.extend(child.rglob(exe))

    # Remove duplicates while preserving search order.
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _find_exe(name: str) -> str:
    """Find an FFmpeg tool without requiring manual Windows PATH setup."""
    exe = f"{name}.exe" if os.name == "nt" else name

    for candidate in _candidate_executables(name):
        if candidate.is_file():
            return str(candidate)

    system = shutil.which(name) or shutil.which(exe)
    if system:
        return system

    searched = "\n".join(f"  - {p}" for p in _candidate_executables(name)[:20])
    raise FileNotFoundError(
        f"Không tìm thấy {exe}. VietDub đã tự tìm nhưng chưa thấy file này.\n"
        f"Các vị trí chính đã kiểm tra:\n{searched}\n"
        f"Bạn cần có cả ffmpeg.exe và ffprobe.exe."
    )


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def ffprobe(video: str) -> dict:
    p = run(
        [
            _find_exe("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=width,height,r_frame_rate,codec_name",
            "-of",
            "json",
            video,
        ]
    )
    return json.loads(p.stdout)


def extract_frames(video: str, out_dir: str, fps: float = 2.0) -> list[Path]:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    pattern = str(d / "frame_%06d.jpg")
    run(
        [
            _find_exe("ffmpeg"),
            "-y",
            "-i",
            video,
            "-vf",
            f"fps={fps}",
            "-q:v",
            "3",
            pattern,
        ]
    )
    return sorted(d.glob("frame_*.jpg"))


def crop_image(src: str, dst: str, x: int, y: int, w: int, h: int) -> None:
    run(
        [
            _find_exe("ffmpeg"),
            "-y",
            "-i",
            src,
            "-vf",
            f"crop={w}:{h}:{x}:{y}",
            "-frames:v",
            "1",
            dst,
        ]
    )
