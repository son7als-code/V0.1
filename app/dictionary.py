import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ProperNameEntry:
    source: str
    normalized: str
    vietnamese: str
    category: str = 'name'
    aliases: list[str] | None = None
    note: str = ''
    def forms(self):
        return {self.source, self.normalized, *(self.aliases or [])}

class ProperNameDictionary:
    def __init__(self, path):
        self.path = Path(path); self.entries = []; self.load()
    def load(self):
        if self.path.exists():
            self.entries = [ProperNameEntry(**x) for x in json.loads(self.path.read_text(encoding='utf-8'))]
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(x) for x in self.entries], ensure_ascii=False, indent=2), encoding='utf-8')
    def upsert(self, entry):
        for i, old in enumerate(self.entries):
            if old.source == entry.source:
                self.entries[i] = entry; self.save(); return
        self.entries.append(entry); self.save()
    def find(self, text):
        return [x for x in self.entries if text in x.forms()]

@dataclass
class OCRCorrection:
    observed: str
    corrected: str
    confidence: float | None = None
    note: str = ''

class OCRMemory:
    def __init__(self, path):
        self.path = Path(path); self.entries = []; self.load()
    def load(self):
        if self.path.exists():
            self.entries = [OCRCorrection(**x) for x in json.loads(self.path.read_text(encoding='utf-8'))]
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(x) for x in self.entries], ensure_ascii=False, indent=2), encoding='utf-8')
    def upsert(self, correction):
        for i, old in enumerate(self.entries):
            if old.observed == correction.observed:
                self.entries[i] = correction; self.save(); return
        self.entries.append(correction); self.save()
    def lookup(self, observed):
        return next((x for x in self.entries if x.observed == observed), None)
    def promote(self, observed, normalized, vietnamese, dictionary, category='name'):
        dictionary.upsert(ProperNameEntry(observed, normalized, vietnamese, category))