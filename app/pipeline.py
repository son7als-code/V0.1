from pathlib import Path
from .sync import DialogueSynchronizer

class DubPipeline:
    def __init__(self, corrector, translator, tts, synchronizer=None):
        self.corrector=corrector; self.translator=translator; self.tts=tts
        self.synchronizer=synchronizer or DialogueSynchronizer()
    def correct_ocr(self, state):
        return self.corrector.correct_cues(state.cues)
    def translate(self, state):
        texts=[c.source_text for c in state.cues]
        for i,c in enumerate(state.cues):
            context=texts[max(0,i-2):min(len(texts),i+3)]
            c.vietnamese=self.translator.translate(c.source_text, context)
        return state.cues
    def synthesize(self, state, output_dir, voice='default'):
        out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
        for c in state.cues:
            if not c.vietnamese: raise ValueError(f'Cue {c.id} chưa có bản dịch')
            c.tts_path=self.tts.synthesize(c.vietnamese,voice,str(out/f'{c.id}.tts.txt'))
        return state.cues
    def validate(self,state):
        state.warnings.clear()
        for c in state.cues:
            if c.timing.end<=c.timing.start: state.warnings.append(f'{c.id}: timing không hợp lệ')
            if not c.source_text.strip(): state.warnings.append(f'{c.id}: câu rỗng')
            if c.confidence<0.75: state.warnings.append(f'{c.id}: OCR confidence thấp ({c.confidence:.2f})')
        return state.warnings