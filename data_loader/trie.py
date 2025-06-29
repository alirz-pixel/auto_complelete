from typing import List, Tuple, Set
from data_loader.db import fetchall

class TrieNode:
    def __init__(self):
        self.children = {}  # 문자 -> TrieNode
        self.is_end_of_word = False
        self.ids = set()  # 해당 단어에 매핑된 DB ID들 (복수 가능)


class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.node_cnt = 1 # root 포함

    def insert(self, word: str, db_id: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
                self.node_cnt += 1
            node = node.children[char]
        node.is_end_of_word = True
        node.ids.add(db_id)

    def search_prefix(self, prefix: str) -> List[Tuple[str, Set[str]]]:
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []  # 접두어에 해당하는 단어 없음
            node = node.children[char]
        return self._collect_all_words(node, prefix)

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

    def _collect_all_words(self, node: TrieNode, prefix: str) -> List[Tuple[str, Set[str]]]:
        results = []
        if node.is_end_of_word:
            results.append((prefix, node.ids))

        for char, child_node in node.children.items():
            results.extend(self._collect_all_words(child_node, prefix + char))
        return results


def a(trie):
    datas = fetchall()

    for data in datas:
        trie.insert(data[1], data[0])


if __name__ == '__main__':
    import tracemalloc

    tracemalloc.start()

    trie = Trie()
    a(trie)

    current, peak = tracemalloc.get_traced_memory()
    print(f"현재 사용량: {current / 1024 / 1024:.2f} MB")
    print(f"최대 사용량: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    while True:
        a = input("자동완성 테스트해보자: ")
        if a == "":
            break

        print(a)
        result = trie.search_prefix(a)
        print(f"결과: {result}")