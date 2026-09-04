from dataclasses import dataclass
from .dictionary import ProperNameDictionary, OCRMemory

@dataclass
class CorrectionResult:
    original: str
    corrected: str
    changed: bool
    reason: str

class OCRCorrector:
    def __init__(self, proper_names: ProperNameDictionary, ocr_memory: OCRMemory):
        self.proper_names = proper_names; self.ocr_memory = ocr_memory
    def correct(self, text):
        m = self.ocr_memory.lookup(text)
        if m:
            return CorrectionResult(text, m.corrected, text != m.corrected, 'project_ocr_memory')
        matches = self.proper_names.find(text)
        if matches:
            e = matches[0]
            return CorrectionResult(text, e.normalized, text != e.normalized, 'proper_name_dictionary')
        return CorrectionResult(text, text, False, 'no_match')
    def correct_cues(self, cues):
        out=[]
        for cue in cues:
            r=self.correct(cue.text); cue.corrected_text=r.corrected; out.append(r)
        return out