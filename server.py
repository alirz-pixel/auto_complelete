from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates

from data_loader.db import fetchall, fetchall_by_ids, fetchall_by_word
from data_loader.trie import Trie

import asyncio
import time
from tqdm import tqdm

templates = Jinja2Templates(directory="template")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trie 준비
data_trie = Trie()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/autocomplete")
async def autocomplete(q: str = Query(..., min_length=1)):
    start = time.time()
    results = data_trie.search_prefix(q)
    done_time = time.time() - start
    print(f"search_time: {done_time}")

    return JSONResponse([
        {"word": word, "ids": list(ids)} for word, ids in results[:15]
    ])

async def get_prefix_matches(query):
    # trie엔 결과가 많이 담겨있음,
    # 단어는 적게, id는 많이 가져가는 것으로 결졍 (사유: 사전이니까 동음이의어는 다 보여줘야 함)
    # 단, 최대 개수는 20개로 한정
    match_ids = []

    nodes = data_trie.search_prefix(query)
    for word, ids in nodes: # 한 단어에 대해
        if word == query: # 이미 조회 당한 친구
            continue

        match_ids.extend(list(ids))
        if len(match_ids) > 20:
            break

    return await fetchall_by_ids(match_ids)

@app.get("/search/words")
async def search_by_ids(word: str, ids: str):
    exact, prefix = await asyncio.gather(
        fetchall_by_ids(ids.split(',')),
        get_prefix_matches(word)
    )
    return exact + prefix

@app.get("/search/word")
async def search_by_word(q: str):
    return fetchall_by_word(q)

def generate_dataset():
    start = time.time()
    datas = fetchall()
    print(f"fetch time: {time.time() - start}")
    # random.shuffle(datas)
    start = time.time()
    for idx in tqdm(range(len(datas))):
        data = datas[idx]
        try:
            cur_word = data[1].replace('-', '')
            cur_word = cur_word.replace('^', ' ')
            data_trie.insert(cur_word, data[0])
        except:
            print(idx, data)
            exit(0)
    print(f"generate trie time: {time.time() - start}")
    print(f"trie node cnt: {data_trie.node_cnt}")


generate_dataset()
