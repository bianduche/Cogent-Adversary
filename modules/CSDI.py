"""
CSDI (Cognitive State Dynamic Inference) - Observer Layer
使用离散隐马尔可夫模型的前向算法，手写numpy实现
"""
import numpy as np
import json
from typing import List, Dict


class CSDI:
    def __init__(self, params_path: str = "csdi_params.json"):
        with open(params_path, "r", encoding="utf-8") as f:
            params = json.load(f)
        self.A = np.array(params["A"])          # 转移矩阵 4x4
        self.B = np.array(params["B"])          # 发射矩阵 4x4
        self.pi = np.array(params["pi"])        # 初始分布
        self.n_states = params["n_states"]      # 4
        self.n_obs = params["n_obs"]            # 4

        # 每个学生独立维护观测序列和alpha向量
        self.student_alphas: Dict[str, np.ndarray] = {}   # 当前前向概率
        self.student_seqs: Dict[str, List[List[int]]] = {}  # 观测序列历史

    def extract_obs(self, answer_correct: bool, response_time: float,
                    semantic_sim: float, edits_ratio: float) -> List[int]:
        """
        将连续观测变量二值化
        O1: 1 if answer_correct else 0
        O2: 1 if response_time > 30 else 0
        O3: 1 if semantic_sim < 0.5 else 0
        O4: 1 if edits_ratio > 0.3 else 0
        """
        O1 = 1 if answer_correct else 0
        O2 = 1 if response_time > 30 else 0
        O3 = 1 if semantic_sim < 0.5 else 0
        O4 = 1 if edits_ratio > 0.3 else 0
        return [O1, O2, O3, O4]

    def _emission_prob(self, state: int, obs: List[int]) -> float:
        """
        计算给定状态下观测向量的联合概率
        假设各观测条件独立: P(O|S) = prod_j P(Oj|Sj)
        """
        prob = 1.0
        for j in range(self.n_obs):
            p_1 = self.B[state, j]
            p_o = p_1 if obs[j] == 1 else (1 - p_1)
            prob *= p_o
        return prob

    def forward(self, student_id: str, obs: List[int]) -> np.ndarray:
        """
        前向算法一步更新
        alpha_t(i) = P(O1...Ot, St=i | lambda)
        返回归一化后的后验概率 P(St=i | O1...Ot)
        """
        if student_id not in self.student_alphas:
            # 初始时刻
            alpha = self.pi * np.array([
                self._emission_prob(i, obs) for i in range(self.n_states)
            ])
            self.student_seqs[student_id] = [obs]
        else:
            prev_alpha = self.student_alphas[student_id]
            # 预测 + 更新
            alpha = np.zeros(self.n_states)
            for j in range(self.n_states):
                alpha[j] = np.sum(prev_alpha * self.A[:, j]) * self._emission_prob(j, obs)
            self.student_seqs[student_id].append(obs)

        # 归一化
        alpha_sum = np.sum(alpha)
        if alpha_sum > 0:
            alpha = alpha / alpha_sum
        else:
            alpha = np.ones(self.n_states) / self.n_states

        self.student_alphas[student_id] = alpha
        return alpha

    def get_dissonance(self, posterior: np.ndarray) -> float:
        """
        认知失调代理 D(t) = 1 - P(S4)
        S4代表完全掌握状态
        """
        return 1.0 - float(posterior[3])

    def get_mastery(self, posterior: np.ndarray) -> float:
        """
        知识掌握度 K_t = P(S4)
        """
        return float(posterior[3])

    def reset_student(self, student_id: str):
        """重置学生状态（新课时时调用）"""
        if student_id in self.student_alphas:
            del self.student_alphas[student_id]
        if student_id in self.student_seqs:
            del self.student_seqs[student_id]
