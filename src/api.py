from config import Config

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/api/test")
async def test_api():
    return {"message": "Hello World"}

app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")

def api():
    import asyncio
    from hypercorn.config import Config as HypConfig
    from hypercorn.asyncio import serve

    hyp_config = HypConfig()
    hyp_config.bind = [Config.API_BIND]

    asyncio.run(serve(app, hyp_config))

if __name__ == '__main__':
    api()