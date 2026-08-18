"""Small JSON file store with readable corrupted-file errors."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile


class StorageError(RuntimeError):
    pass


class JsonStore:
    def save(self, path: Path, data: dict | list) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path: Path | None = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
                temp_path = Path(tmp.name)
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp.write("\n")
            temp_path.replace(path)
        except OSError as exc:
            raise StorageError(f"Could not write project file: {path.name}") from exc
        finally:
            if temp_path and temp_path.exists() and temp_path != path:
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def load(self, path: Path) -> dict | list:
        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as exc:
            raise StorageError(f"Missing project file: {path.name}") from exc
        except json.JSONDecodeError as exc:
            raise StorageError(f"Corrupted project file: {path.name}") from exc
        except OSError as exc:
            raise StorageError(f"Could not read project file: {path.name}") from exc
