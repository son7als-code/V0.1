from __future__ import annotations
import json, subprocess
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def ffprobe(video: str) -> dict:
    p = run(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,r_frame_rate,codec_name','-of','json',video])
    return json.loads(p.stdout)


def extract_frames(video: str, out_dir: str, fps: float = 2.0) -> list[Path]:
    d = Path(out_dir); d.mkdir(parents=True, exist_ok=True)
    pattern = str(d / 'frame_%06d.jpg')
    run(['ffmpeg','-y','-i',video,'-vf',f'fps={fps}','-q:v','3',pattern])
    return sorted(d.glob('frame_*.jpg'))


def crop_image(src: str, dst: str, x: int, y: int, w: int, h: int) -> None:
    run(['ffmpeg','-y','-i',src,'-vf',f'crop={w}:{h}:{x}:{y}','-frames:v','1',dst])
