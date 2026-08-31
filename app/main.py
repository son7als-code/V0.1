from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import requests
from faster_whisper import WhisperModel


def srt_time(seconds: float) -> str:
    ms = max(0, int(round(seconds * 1000)))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def load_glossary(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str, glossary: dict[str, str]) -> str:
    for wrong, right in glossary.items():
        text = text.replace(wrong, right)
    return text.strip()


def translate(text: str, glossary: dict[str, str]) -> str:
    api_key = os.environ.get("TRANSLATOR_API_KEY")
    if not api_key:
        raise RuntimeError("Thiếu TRANSLATOR_API_KEY. V0.1 cần API dịch OpenAI-compatible để dịch Trung → Việt.")
    base_url = os.environ.get("TRANSLATOR_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("TRANSLATOR_MODEL", "gpt-4o-mini")
    glossary_text = "\n".join(f"- {k} => {v}" for k, v in glossary.items())
    prompt = (
        "Dịch câu tiếng Trung sau sang tiếng Việt tự nhiên, giữ nguyên tên riêng theo bảng quy đổi. "
        "Không giải thích, chỉ trả về bản dịch.\n\n"
        f"Bảng tên/OCR:\n{glossary_text}\n\nTiếng Trung:\n{text}"
    )
    r = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0.1, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def run(input_file: Path, output_file: Path, model_name: str, glossary_file: Path) -> None:
    glossary = load_glossary(glossary_file)
    model = WhisperModel(model_name, device="auto", compute_type="auto")
    segments, _ = model.transcribe(str(input_file), language="zh", vad_filter=True)
    rows = []
    for i, seg in enumerate(segments, 1):
        cn = normalize(seg.text, glossary)
        if not cn:
            continue
        vi = translate(cn, glossary)
        rows.append(f"{i}\n{srt_time(seg.start)} --> {srt_time(seg.end)}\n{vi}\n")
    output_file.write_text("\n".join(rows), encoding="utf-8")
    print(f"Đã tạo: {output_file}")


def main() -> None:
    p = argparse.ArgumentParser(description="Chinese → Vietnamese SRT translator")
    p.add_argument("input", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--whisper-model", default="small")
    p.add_argument("--glossary", type=Path, default=Path("glossary.json"))
    args = p.parse_args()
    output = args.output or args.input.with_name(args.input.stem + "_vi.srt")
    run(args.input, output, args.whisper_model, args.glossary)


if __name__ == "__main__":
    main()
