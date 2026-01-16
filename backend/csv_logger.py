import csv
import os
from dataclasses import dataclass, field
from typing import Dict, Any, Iterable, Optional


@dataclass
class CSVLogger:
    path: str
    fieldnames: Iterable[str]
    flush_every: int = 200  # flush every N rows (performance)
    _file: Optional[object] = field(default=None, init=False)
    _writer: Optional[csv.DictWriter] = field(default=None, init=False)
    _rows_since_flush: int = field(default=0, init=False)

    def open(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        is_new = not os.path.exists(self.path) or os.path.getsize(self.path) == 0

        self._file = open(self.path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=list(self.fieldnames))

        if is_new:
            self._writer.writeheader()
            self._file.flush()

    def log(self, row: Dict[str, Any]) -> None:
        if self._writer is None or self._file is None:
            raise RuntimeError("CSVLogger not opened. Call open() first.")

        self._writer.writerow(row)
        self._rows_since_flush += 1
        if self._rows_since_flush >= self.flush_every:
            self._file.flush()
            self._rows_since_flush = 0

    def flush(self) -> None:
        if self._file is not None:
            self._file.flush()
            self._rows_since_flush = 0

    def close(self) -> None:
        if self._file is not None:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
            self._rows_since_flush = 0
