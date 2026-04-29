import ctypes
from dataclasses import dataclass
from pathlib import Path

import psutil
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

MB = 1024 * 1024
HISTORY_SIZE = 24
MODEL_MIN_POINTS = 8
MODEL_RISK_CAP = 55.0


@dataclass
class MonitorData:
    second: int
    memory_mb: float
    cpu_percent: float
    score: int
    leak: bool


class LeakResult(ctypes.Structure):
    _fields_ = [
        ("score", ctypes.c_int),
        ("leak", ctypes.c_int),
    ]


def load_c_core():
    dll_path = Path(__file__).resolve().parent.parent / "c_core" / "monitor_core.dll"
    if not dll_path.exists():
        raise RuntimeError("C core is not built. Run c_core/build.ps1 first.")

    library = ctypes.CDLL(str(dll_path))
    library.calculate_leak.argtypes = [
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.POINTER(LeakResult),
    ]
    library.calculate_leak.restype = ctypes.c_int
    return library


class Monitor:
    def __init__(self) -> None:
        self.core = load_c_core()
        self.second = 0
        self.memory_history = []
        self.cpu_history = []

        total_memory_mb = psutil.virtual_memory().total / MB
        self.default_threshold_mb = max(500.0, total_memory_mb * 0.85)
        psutil.cpu_percent(interval=None)

    def next_data(self, threshold: float = 420.0) -> MonitorData:
        self.second += 1

        system_memory = psutil.virtual_memory()
        memory_mb = system_memory.used / MB
        cpu_percent = psutil.cpu_percent(interval=None)

        model_score = self._model_score(memory_mb, cpu_percent)
        self._record_history(memory_mb, cpu_percent)
        score, leak = self._calculate_leak(memory_mb, cpu_percent, threshold, system_memory.percent, model_score)

        return MonitorData(self.second, memory_mb, cpu_percent, score, leak)

    def _calculate_leak(
        self,
        memory_mb: float,
        cpu_percent: float,
        threshold: float,
        memory_percent: float,
        model_score: float,
    ) -> tuple[int, bool]:
        result = LeakResult()

        ok = self.core.calculate_leak(
            memory_mb,
            cpu_percent,
            threshold,
            memory_percent,
            model_score,
            ctypes.byref(result),
        )
        if not ok:
            raise RuntimeError("C core failed to calculate leak score.")

        return result.score, bool(result.leak)

    def _model_score(self, memory_mb: float, cpu_percent: float) -> float:
        if len(self.memory_history) < MODEL_MIN_POINTS:
            return 0.0

        history_points = list(zip(self.memory_history, self.cpu_history))
        current_point = [[memory_mb, cpu_percent]]

        model = make_pipeline(
            StandardScaler(),
            IsolationForest(
                n_estimators=80,
                contamination=0.15,
                random_state=42,
            ),
        )
        model.fit(history_points)

        history_scores = model.score_samples(history_points)
        current_score = float(model.score_samples(current_point)[0])
        score_floor = min(history_scores)
        score_ceiling = max(history_scores)
        score_range = max(score_ceiling - score_floor, 1e-6)

        anomaly_score = ((score_ceiling - current_score) / score_range) * MODEL_RISK_CAP
        if model.predict(current_point)[0] == -1:
            anomaly_score = max(anomaly_score, 45.0)

        return max(0.0, min(MODEL_RISK_CAP, anomaly_score))

    def _record_history(self, memory_mb: float, cpu_percent: float) -> None:
        self.memory_history.append(memory_mb)
        self.cpu_history.append(cpu_percent)
        if len(self.memory_history) > HISTORY_SIZE:
            self.memory_history.pop(0)
            self.cpu_history.pop(0)
