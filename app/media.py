from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _find_exe(name: str) -> str:
    """Find FFmpeg tools without requiring Windows PATH configuration."""
    exe = f"{name}.exe" if os.name == "nt" else name
    candidates = [
        ROOT / "ffmpeg" / "bin" / exe,
        ROOT / "ffmpeg" / exe,
        ROOT / "bin" / exe,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    system = shutil.which(name)
    if system:
        return system
    raise FileNotFoundError(
        f"Không tìm thấy {exe}. Đặt FFmpeg vào: {ROOT / 'ffmpeg' / 'bin'} "
        f"(cần {exe} và ffprobe.exe), hoặc cài FFmpeg vào PATH của Windows."
    )


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def ffprobe(video: str) -> dict:
    p = run([_find_exe('ffprobe'), '-v', 'error', '-show_entries', 'format=duration:stream=width,height,r_frame_rate,codec_name', '-of', 'json', video])
    return json.loads(p.stdout)


def extract_frames(video: str, out_dir: str, fps: float = 2.0) -> list[Path]:
    d = Path(out_dir); d.mkdir(parents=True, exist_ok=True)
    pattern = str(d / 'frame_%06d.jpg')
    run([_find_exe('ffmpeg'), '-y', '-i', video, '-vf', f'fps={fps}', '-q:v', '3', pattern])
    return sorted(d.glob('frame_*.jpg'))


def crop_image(src: str, dst: str, x: int, y: int, w: int, h: int) -> None:
    run([_find_exe('ffmpeg'), '-y', '-i', src, '-vf', f'crop={w}:{h}:{x}:{y}', '-frames:v', '1', dst])
