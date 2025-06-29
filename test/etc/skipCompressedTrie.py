from typing import List, Tuple, Set
from data_loader.db import fetchall
import tracemalloc

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
            # word는 계속해서 짤리면서 child로 내려감
            for edge, child in node.children.items():
                # 공통된 length 재기
                common_len = self._common_prefix_len(word, edge)
                if common_len == 0: # 공통된 부분이 없으면 해당 child는 스킵
                    continue

                # edge보다 공통된 부분이 짧으면 기존 노드를 분할 해야 함
                if common_len < len(edge):
                    # 분할될 node를 새로 만들기
                    new_child = CompressedTrieNode()
                    new_child.children[edge[common_len:]] = child
                    new_child.is_end_of_word = False

                    node.children[edge[:common_len]] = new_child
                    del node.children[edge] # 원래 연결된 경로를 자르고
                    node = new_child # 새롭게 만든 node로 경로 연결

                    if common_len == len(word):
                        node.is_end_of_word = True
                        node.ids.add(db_id)
                        return

                    word = word[common_len:] # word는 사용한 만큼 짤림
                    break

                if common_len == len(edge): # node와 현 word의 공통된 부분이 일치
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
                    # 해당 node를 기준으로 모든 child 수집
                    path += prefix
                    return self._collect_all_words(child, path + edge[len(prefix):])

                if prefix.startswith(edge):
                    # prefix: "가는 말이", edge: "가는"
                    # 다음 child로 이동
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
        # edge와 prefix의 일치하는 length를 재는 함수
        # skip_cnt를 잘 구현해야 함
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        return i


class SkipCompressedTrie(CompressedTrie):
    # skip을 한 번이라도 안 썼다면 더 이상 사용하면 안됨
    # 포함 여부로 할거면 상관 없긴 함
    def search_skip_prefix(self, prefix: str, skip_cnt: int = 0, node=None, path="") -> List[Tuple[str, Set[str]]]:
        if node is None:
            node = self.root

        results = []

        for edge, child in node.children.items():
            matches = self._common_prefix_len_with_edge_skip(prefix, edge, skip_cnt)
            for match_len, used_skip in matches:
                # print(f"path: {path},  edge: {edge},  prefix: {prefix},  match_len: {match_len},  used_skip: {used_skip}")
                if match_len - used_skip == len(prefix):
                    # prefix 전부 매칭됨 (edge가 더 길든 말든)
                    results.extend(self._collect_all_words(child, path + edge))
                elif match_len > 0: # == len(edge):
                    # 일부 매칭됨 → prefix 자르고 재귀
                    next_prefix = prefix[match_len - used_skip:]  # prefix는 그대로 진행
                    next_skip = 0 if used_skip == 0 else skip_cnt - used_skip # 일부 매칭으로 할거면, skip_cnt - used_skip 만
                    # print(f"path: {path},  edge: {edge},  next_prefix: {next_prefix},  next_skip: {next_skip}")
                    results.extend(
                        self.search_skip_prefix(next_prefix, next_skip, child, path + edge)
                    )

        return results

    def _common_prefix_len_with_edge_skip(self, prefix: str, edge: str, skip_cnt: int) -> Tuple[int, int]:
        """
        edge를 skip_cnt만큼 건너뛰면서 prefix와 최대한 매칭
        반환: (prefix와 매칭된 edge 길이, 사용한 skip 수)
        """
        results = []
        for skip_used in range(skip_cnt + 1):
            match_len = 0
            i, j = 0, skip_used
            while i < len(prefix) and j < len(edge) and prefix[i] == edge[j]:
                i += 1
                j += 1
                match_len += 1

            if match_len + skip_used > 0:
                results.append((match_len + skip_used, skip_used))
        return results




def a(trie):
    datas = fetchall()

    # random.shuffle(datas)

    print(datas[0])
    start = time.time()
    for idx in tqdm(range(len(datas[:60000]))):
        data = datas[idx]
        cur_word = data[1].replace('-', '')
        cur_word = cur_word.replace('^', ' ')
        trie.insert(cur_word, data[0])
    print(time.time() - start)

if __name__ == '__main__':
    import random
    import time
    from tqdm import tqdm
    import tracemalloc

    # tracemalloc.start()

    trie = SkipCompressedTrie()
    a(trie)

    current, peak = tracemalloc.get_traced_memory()
    # print(f"현재 사용량: {current / 1024 / 1024:.2f} MB")
    # print(f"최대 사용량: {peak / 1024 / 1024:.2f} MB")
    #
    # tracemalloc.stop()

    while True:
        b = input("자동완성 테스트해보자: ")
        if b == "":
            break
        c = int(input("skip: "))

        # result = trie.search_prefix(a)
        result = trie.search_skip_prefix(b, c)
        print(f"결과: {result}")