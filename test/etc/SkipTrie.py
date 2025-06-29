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
        self.node_cnt = 1  # root 포함

    def insert(self, word: str, db_id: str):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
                self.node_cnt += 1
            node = node.children[char]
        node.is_end_of_word = True
        node.ids.add(db_id)

    def search_skip_prefix(self, prefix: str, skip_cnt=0, node=None):
        if node == None:
            node = self.root

        if skip_cnt == 0:
            return self.search_prefix(prefix, node)

        combine_results = self.search_prefix(prefix, node)
        for child_char in node.children:
            results = self.search_skip_prefix(prefix, skip_cnt - 1, node.children[child_char])

            for result in results:
                combine_results.append((child_char + result[0], result[1]))
        return combine_results

    def search_prefix(self, prefix: str, node=None) -> List[Tuple[str, Set[str]]]:
        if node == None:
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

    # for data in datas[:6000]:
    for data in datas:
        trie.insert(data[1], data[0])
    print(datas[0])


if __name__ == '__main__':
    import time
    import tracemalloc

    tracemalloc.start()

    trie = Trie()
    trie.insert("apple", "")

    a(trie)

    current, peak = tracemalloc.get_traced_memory()
    print(f"현재 사용량: {current / 1024 / 1024:.2f} MB")
    print(f"최대 사용량: {peak / 1024 / 1024:.2f} MB")

    tracemalloc.stop()

    while True:
        a = input("자동완성 테스트해보자: ")
        if a == "":
            break
        skip_cnt = int(input("skip 몇번?: "))

        start = time.time()
        result = trie.search_skip_prefix(a, skip_cnt)
        print(f"search_time: {time.time() - start}")
        print(f"결과: {result}")
