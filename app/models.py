from dataclasses import dataclass, field, asdict
from typing import Optional

@dataclass
class TimeRange:
    start: float
    end: float
    @property
    def duration(self):
        return max(0.0, self.end - self.start)

@dataclass
class SubtitleRegion:
    x: float
    y: float
    width: float
    height: float
    def validate(self):
        if not (0 <= self.x <= 1 and 0 <= self.y <= 1):
            raise ValueError('x/y must be normalized 0..1')
        if not (0 < self.width <= 1 and 0 < self.height <= 1):
            raise ValueError('width/height must be in 0..1')
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError('subtitle region exceeds video bounds')

@dataclass
class SubtitleCue:
    id: str
    timing: TimeRange
    text: str
    confidence: float = 1.0
    speaker: Optional[str] = None
    corrected_text: Optional[str] = None
    vietnamese: Optional[str] = None
    tts_path: Optional[str] = None
    @property
    def source_text(self):
        return self.corrected_text if self.corrected_text is not None else self.text

@dataclass
class ProjectConfig:
    project_id: str
    source_video: str
    subtitle_region: Optional[SubtitleRegion] = None
    output_resolution: str = '1080p'
    keep_original_bgm: bool = True
    export_srt: bool = True

@dataclass
class ProjectState:
    config: ProjectConfig
    cues: list[SubtitleCue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    def to_dict(self):
        return asdict(self)