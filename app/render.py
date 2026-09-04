from __future__ import annotations
import subprocess
from pathlib import Path

RESOLUTIONS={'720p':(1280,720),'1080p':(1920,1080),'2K':(2560,1440)}

def _run(cmd):
    return subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

def srt_time(sec):
    ms=max(0,int(round(sec*1000))); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def write_srt(cues, path):
    lines=[]
    for i,c in enumerate(cues,1):
        lines += [str(i), f"{srt_time(c['start'])} --> {srt_time(c['end'])}", c.get('vietnamese',''), '']
    Path(path).write_text('\n'.join(lines),encoding='utf-8')

def render(video, cues, tts_files, out, resolution='1080p', mask_original=True):
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    w,h=RESOLUTIONS[resolution]
    # Build a single narration track with each TTS clip delayed to its cue start.
    inputs=[video]; filters=[]; labels=[]
    for i,(cue,audio) in enumerate(zip(cues,tts_files),1):
        inputs += [audio]
        delay=max(0,int(cue['start']*1000))
        filters.append(f'[{i}:a]adelay={delay}:all=1[a{i}]'); labels.append(f'[a{i}]')
    if labels:
        filters.append(''.join(labels)+f'amix=inputs={len(labels)}:duration=longest:normalize=0[tts]')
        audio_map='[mix]'
        filters.append('[0:a][tts]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[mix]')
    else: audio_map='0:a'
    # Mask subtitle area at the bottom; Vietnamese subtitles are burned by FFmpeg when SRT exists.
    srt=Path(out).with_suffix('.srt'); write_srt(cues,srt)
    vf=f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2'
    if mask_original: vf += ',drawbox=x=0:y=ih*0.78:w=iw:h=ih*0.22:color=black@0.0:t=fill'
    cmd=['ffmpeg','-y','-i',video]
    for a in tts_files: cmd += ['-i',a]
    cmd += ['-filter_complex',';'.join(filters),'-map','0:v:0','-map',audio_map,'-vf',vf,'-c:v','libx264','-preset','medium','-crf','20','-c:a','aac','-b:a','192k','-shortest',out]
    _run(cmd)
    return str(out),str(srt)
