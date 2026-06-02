"""
KGAR (Knowledge Graph Argument Retrieval) - Executor Layer
从知识图谱中检索导师路径和质疑者路径
"""
import networkx as nx
import json
from typing import List, Tuple, Set
import random


class KGAR:
    def __init__(self, kg_path: str = "welding_kg.graphml"):
        self.G = nx.read_graphml(kg_path)
        # 将节点标签映射到节点ID
        self.label_to_id = {}
        for node_id, data in self.G.nodes(data=True):
            label = data.get("label", node_id)
            self.label_to_id[label] = node_id

        # 白名单：教材中存在的路径节点（简化版：所有节点都在白名单中）
        self.whitelist = set(self.label_to_id.keys())

    def find_paths(self, entity: str, k: int = 3) -> Tuple[List[str], List[str]]:
        """
        从entity出发，找所有k-hop内到达CauseFactor节点的简单路径
        返回两条语义差异最大的路径
        """
        if entity not in self.label_to_id:
            # 如果实体不在图谱中，返回默认路径
            default = [entity, "未知原因", "需进一步分析"]
            return default, default

        start_id = self.label_to_id[entity]

        # 找所有k-hop内的简单路径，终点是CauseFactor类型
        all_paths = []
        cause_nodes = [
            n for n, d in self.G.nodes(data=True)
            if d.get("node_type") == "CauseFactor"
        ]

        for target_id in cause_nodes:
            try:
                for path in nx.all_simple_paths(self.G, start_id, target_id, cutoff=k):
                    # 转换为标签列表
                    path_labels = [self.G.nodes[n].get("label", n) for n in path]
                    # 白名单过滤
                    if all(p in self.whitelist for p in path_labels):
                        all_paths.append(path_labels)
            except nx.NetworkXNoPath:
                continue

        if len(all_paths) < 2:
            # 路径不足，生成一些基于邻居的默认路径
            neighbors = list(self.G.neighbors(start_id))[:5]
            for nb in neighbors:
                nb_label = self.G.nodes[nb].get("label", nb)
                path = [entity, nb_label]
                # 再扩展一层
                for nb2 in list(self.G.neighbors(nb))[:2]:
                    nb2_label = self.G.nodes[nb2].get("label", nb2)
                    all_paths.append([entity, nb_label, nb2_label])

        if len(all_paths) < 2:
            default_a = [entity, "材料因素", "热影响区脆化"]
            default_b = [entity, "工艺参数", "焊接电流过大"]
            return default_a, default_b

        return self._select_diverse_pair(all_paths)

    def _select_diverse_pair(self, paths: List[List[str]]) -> Tuple[List[str], List[str]]:
        """
        选两条语义差异最大的路径（简单版：长度差异最大）
        进阶版可用Sentence-BERT编码后选cosine距离最大
        """
        best_pair = (paths[0], paths[1])
        best_diff = abs(len(paths[0]) - len(paths[1]))

        # 同时也考虑路径内容差异（Jaccard距离）
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                set_i = set(paths[i])
                set_j = set(paths[j])
                union = set_i | set_j
                inter = set_i & set_j
                jaccard_dist = 1.0 - (len(inter) / len(union)) if union else 0.0
                length_diff = abs(len(paths[i]) - len(paths[j]))
                # 综合评分
                score = jaccard_dist + 0.1 * length_diff
                if score > best_diff:
                    best_diff = score
                    best_pair = (paths[i], paths[j])

        return best_pair
