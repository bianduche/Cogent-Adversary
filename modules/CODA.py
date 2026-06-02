"""
CODA (Cognitive Dissonance-Aware Control) - Controller Layer
计算最优对抗强度 alpha(t)
"""
from typing import List
import numpy as np
from math import sin, pi


class CODA:
    def __init__(self, eta: float = 0.35, delta: float = 0.28, T: int = 10):
        self.eta = eta
        self.delta = delta
        self.T = T
        self.epsilon = 1e-6
        self.ref = self._build_ref(T)

    def _build_ref(self, T: int = 10) -> List[float]:
        """
        构建课程级倒U型参考轨迹 D_ref(t)
        """
        T_mid = T // 2
        ref = []
        for t in range(T):
            if t <= T_mid:
                d = 0.2 + 0.5 * sin(pi * t / (2 * T_mid))
            else:
                d = 0.7 - 0.5 * (t - T_mid) / (T - T_mid)
            ref.append(max(0.2, d))
        return ref

    def solve(self, D_t: float, K_t: float, t: int) -> float:
        """
        解析解公式:
        alpha = clip((D_ref[t] - D_t + delta * K_t) / (eta * (1 - K_t) + epsilon), 0, 1)
        """
        if t < 0 or t >= len(self.ref):
            t = max(0, min(t, len(self.ref) - 1))

        numerator = self.ref[t] - D_t + self.delta * K_t
        denominator = self.eta * (1.0 - K_t) + self.epsilon
        alpha = numerator / denominator
        return float(np.clip(alpha, 0.0, 1.0))
