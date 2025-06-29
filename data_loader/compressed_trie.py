from typing import List, Tuple, Set
from .db import fetchall

class CompressedTrieNode:
    def __init__(self):
        self.children = {}  # 문자열(edge) -> CompressedTrieNode
        self.is_end_of_word = False
        self.ids = set()  # 해당 단어에 매핑된 DB ID들 (복수 가능)


class CompressedTrie:
    def __init__(self):
        self.root = CompressedTrieNode()
        self.node_cnt = 1  # root 포함

    def insert(self, word: str, db_id: str):
        node = self.root
        while word:
            for edge, child in node.children.items():
                common_len = self._common_prefix_len(word, edge)
                if common_len == 0:
                    continue

                if common_len < len(edge):
                    # 기존 edge 분할
                    new_child = CompressedTrieNode()
                    new_child.children[edge[common_len:]] = child
                    new_child.is_end_of_word = False

                    node.children[edge[:common_len]] = new_child
                    del node.children[edge]
                    node = new_child

                    if common_len == len(word):
                        node.is_end_of_word = True
                        node.ids.add(db_id)
                        return

                    word = word[common_len:]
                    break

                if common_len == len(edge):
                    word = word[common_len:]
                    node = child
                    break
            else:
                # 일치하는 edge가 없음
                node.children[word] = CompressedTrieNode()
                node.children[word].is_end_of_word = True
                node.children[word].ids.add(db_id)
                self.node_cnt += 1
                return

        node.is_end_of_word = True
        node.ids.add(db_id)

    def search_prefix(self, prefix: str):
        node = self.root
        path = ""

        while prefix:
            for edge, child in node.children.items():
                common_len = self._common_prefix_len(prefix, edge)

                if common_len == 0:
                    continue

                if edge.startswith(prefix):
                    # 예: edge = "가는 말이 고와야", prefix = "가는 말이"
                    path += prefix
                    return self._collect_all_words(child, path + edge[len(prefix):])

                if prefix.startswith(edge):
                    prefix = prefix[len(edge):]
                    path += edge
                    node = child
                    break
            else:
                return []

        return self._collect_all_words(node, path)

    def print_trie(self, node=None, prefix="", depth=0):
        if node is None:
            node = self.root  # 전역 CompressedTrie 객체 사용
            print("[Trie 구조]")

        indent = "    " * depth
        for edge, child in node.children.items():
            node_info = f"{indent}└─ {edge}"
            if child.is_end_of_word:
                node_info += f" (EOW, ids={list(child.ids)})"
            print(node_info)
            self.print_trie(child, prefix + edge, depth + 1)

    def _collect_all_words(self, node: CompressedTrieNode, prefix: str) -> List[Tuple[str, Set[str]]]:
        results = []
        if node.is_end_of_word:
            results.append((prefix, node.ids))

        for edge, child in node.children.items():
            results.extend(self._collect_all_words(child, prefix + edge))
        return results

    def _common_prefix_len(self, a: str, b: str) -> int:
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        return i


def a(trie):
    datas = fetchall()

    random.shuffle(datas)

    print(datas[0])
    start = time.time()
    for idx in tqdm(range(len(datas))):
        data = datas[idx]
        trie.insert(data[1], data[0])
    print(time.time() - start)

if __name__ == '__main__':
    import random
    import time
    from tqdm import tqdm
    import tracemalloc

    tracemalloc.start()

    trie = CompressedTrie()
    a(trie)

    current, peak = tracemalloc.get_traced_memory()
    print(f"현재 사용량: {current / 1024 / 1024:.2f} MB")
    print(f"최대 사용량: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    while True:
        a = input("자동완성 테스트해보자: ")
        if a == "":
            break

        result = trie.search_prefix(a)
        print(f"결과: {result}")