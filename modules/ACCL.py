"""
ACCL (Adversarial Consistency Control Layer) - Safety Layer
校验LLM回复是否偏离知识路径
"""
import jieba
from typing import List, Tuple, Set


class ACCL:
    def __init__(self):
        # 加载自定义词典（如果有）
        pass

    def extract_entities(self, text: str) -> Set[str]:
        """
        使用jieba分词提取中文词汇
        过滤掉单字和常见停用词
        """
        words = jieba.lcut(text)
        # 过滤单字、数字、标点
        entities = set()
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        for w in words:
            w = w.strip()
            if len(w) >= 2 and w not in stopwords and not w.isdigit():
                entities.add(w)
        return entities

    def check(self, response: str, path: List[str]) -> Tuple[bool, float]:
        """
        校验回复是否偏离知识路径
        偏离度 = |extracted_entities - path_entities| / |extracted_entities|
        若delta > 0.2，判定为失败

        附加校验：检查回复中是否包含路径首节点（LCA的承认语句简单版）
        """
        extracted = self.extract_entities(response)
        path_entities = set(path)

        if not extracted:
            # 如果没有提取到实体，认为通过（避免空回复被误判）
            return True, 0.0

        # 计算偏离度：回复中不在路径里的实体占比
        outside = extracted - path_entities
        delta = len(outside) / len(extracted)

        # 附加校验：包含路径首节点
        lca_check = path[0] in response if path else True

        passed = (delta <= 0.2) and lca_check
        return passed, float(delta)
