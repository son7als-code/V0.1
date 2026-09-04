import json
from pathlib import Path
from app.models import TimeRange, SubtitleCue, ProjectConfig, ProjectState, SubtitleRegion
from app.dictionary import ProperNameDictionary, ProperNameEntry, OCRMemory, OCRCorrection
from app.correction import OCRCorrector
from app.engines import MockTranslator, MockTTS
from app.pipeline import DubPipeline
from app.sync import DialogueSynchronizer

def test_region_validation():
    SubtitleRegion(.1,.8,.8,.15).validate()

def test_project_ocr_overrides_dictionary(tmp_path):
    d=ProperNameDictionary(tmp_path/'names.json')
    d.upsert(ProperNameEntry('林野','林野','Lâm Dã'))
    m=OCRMemory(tmp_path/'ocr.json')
    m.upsert(OCRCorrection('林叶','林野',.61))
    r=OCRCorrector(d,m).correct('林叶')
    assert r.corrected=='林野' and r.reason=='project_ocr_memory'

def test_promote_ocr_to_long_term(tmp_path):
    d=ProperNameDictionary(tmp_path/'names.json')
    m=OCRMemory(tmp_path/'ocr.json')
    m.promote('林叶','林野','Lâm Dã',d,'character')
    assert d.find('林叶')[0].vietnamese=='Lâm Dã'

def test_full_pipeline(tmp_path):
    d=ProperNameDictionary(tmp_path/'names.json')
    m=OCRMemory(tmp_path/'ocr.json')
    m.upsert(OCRCorrection('林叶','林野',.61))
    state=ProjectState(ProjectConfig('p1','input.mp4'),[SubtitleCue('001',TimeRange(0,3),'林叶，你来了。',.61)])
    p=DubPipeline(OCRCorrector(d,m),MockTranslator(),MockTTS())
    p.correct_ocr(state); p.translate(state); p.synthesize(state,tmp_path/'tts')
    assert state.cues[0].source_text=='林野，你来了。'
    assert state.cues[0].vietnamese.startswith('[VI]')
    assert Path(state.cues[0].tts_path).exists()

def test_sync_warns_when_tts_is_too_long():
    r=DialogueSynchronizer().plan('1',2,3)
    assert r.speed_factor==1.25 and r.warning

def test_dictionary_is_persistent_json(tmp_path):
    p=tmp_path/'names.json'; d=ProperNameDictionary(p)
    d.upsert(ProperNameEntry('洛宁','洛宁','Lạc Ninh'))
    data=json.loads(p.read_text(encoding='utf-8'))
    assert data[0]['vietnamese']=='Lạc Ninh'