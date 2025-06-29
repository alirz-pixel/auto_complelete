import uvicorn

if __name__ == '__main__':
    uvicorn.run("server:app", port=5235, reload=True)