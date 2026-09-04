from __future__ import annotations
import re
from collections import Counter
from pathlib import Path


def clean_ocr(text: str) -> str:
    text = re.sub(r'\s+', '', text or '')
    return text.strip('。．.，,、:：;；')


def ocr_image(path: str) -> tuple[str, float]:
    try:
        from paddleocr import PaddleOCR
    except ImportError as e:
        raise RuntimeError('Chưa cài PaddleOCR. Chạy: pip install -r requirements.txt') from e
    # Lazy model creation keeps GUI startup light.
    global _OCR
    if '_OCR' not in globals():
        _OCR = PaddleOCR(lang='ch')
    result = _OCR.predict(str(path))
    texts, scores = [], []
    for page in result:
        data = page.json if hasattr(page, 'json') else page
        if isinstance(data, str):
            import json; data = json.loads(data)
        if isinstance(data, dict):
            for key in ('rec_texts','text'):
                vals = data.get(key)
                if vals:
                    texts.extend(vals if isinstance(vals,list) else [vals]); break
            vals = data.get('rec_scores') or data.get('scores') or []
            scores.extend([float(x) for x in vals])
    text = clean_ocr(''.join(texts))
    return text, (sum(scores)/len(scores) if scores else (1.0 if text else 0.0))


def build_cues(frame_texts: list[tuple[float,str,float]], min_repeat: int = 1):
    # frame_texts: (time, text, confidence). Consecutive equal OCR is one subtitle cue.
    cues=[]
    current=None
    for t,text,conf in frame_texts:
        if not text: continue
        if current and text == current['text'] and t-current['last'] <= 1.1:
            current['last']=t; current['confidence']=(current['confidence']+conf)/2
        else:
            if current: cues.append(current)
            current={'start':max(0,t-0.5),'last':t,'text':text,'confidence':conf}
    if current: cues.append(current)
    for i,c in enumerate(cues,1):
        c['end']=c['last']+0.5; c['id']=str(i)
    return cues
