from dataclasses import dataclass

@dataclass
class SyncDecision:
    cue_id: str
    target_duration: float
    tts_duration: float
    speed_factor: float
    warning: str | None = None

class DialogueSynchronizer:
    def __init__(self, min_speed=0.80, max_speed=1.25):
        self.min_speed=min_speed; self.max_speed=max_speed
    def plan(self, cue_id, target_duration, tts_duration):
        if tts_duration <= 0:
            return SyncDecision(cue_id,target_duration,tts_duration,1.0,'empty_tts')
        speed=tts_duration/max(target_duration,0.001)
        warning=None
        if speed>self.max_speed:
            warning='TTS dài: cần time-stretch mạnh hoặc nới timing.'; speed=self.max_speed
        elif speed<self.min_speed:
            warning='TTS ngắn: nên thêm pause hoặc giữ tốc độ tự nhiên.'; speed=self.min_speed
        return SyncDecision(cue_id,target_duration,tts_duration,speed,warning)