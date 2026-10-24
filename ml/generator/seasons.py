"""Kalender simulasi: intensitas musim ramai s(t) dan libur Lebaran (bagian 7).

Semua tanggal di dalam generator disimpan sebagai indeks hari sejak PERIOD_START.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from generator import config


class Calendar:
    def __init__(self) -> None:
        self.start = config.PERIOD_START
        n_days = (config.CALENDAR_END - self.start).days + 1
        self.end_idx = self.index(config.PERIOD_END)

        self.intensity = np.zeros(n_days)
        for start, end, s_start, s_end, _ in config.SEASONS:
            i0, i1 = self.index(start), self.index(end)
            self.intensity[i0 : i1 + 1] = np.linspace(s_start, s_end, i1 - i0 + 1)

        self.closed = np.zeros(n_days, dtype=bool)
        for start, end, _ in config.CLOSURES:
            i0, i1 = max(self.index(start), 0), self.index(end)
            self.closed[i0 : i1 + 1] = True
            self.intensity[i0 : i1 + 1] = 0.0
        self._closed_cumsum = np.concatenate([[0], np.cumsum(self.closed)])

    def index(self, d: date) -> int:
        return (d - self.start).days

    def to_date(self, idx: int) -> date:
        return self.start + timedelta(days=int(idx))

    def season(self, idx: int) -> float:
        return float(self.intensity[idx])

    def is_working_day(self, idx: int) -> bool:
        return self.to_date(idx).weekday() != 6 and not self.closed[idx]

    def closed_days(self, start_idx: int, n_days: np.ndarray) -> np.ndarray:
        """Jumlah hari libur di rentang [start_idx, start_idx + n_days)."""
        last = len(self.closed)
        end = np.minimum(start_idx + n_days, last)
        return self._closed_cumsum[end] - self._closed_cumsum[min(start_idx, last)]

    def split_of(self, idx: int) -> str:
        d = self.to_date(idx)
        for name, start, end in config.SPLITS:
            if start <= d <= end:
                return name
        raise ValueError(f"Tanggal {d} di luar periode split")
