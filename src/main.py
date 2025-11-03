from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from redis.client import PubSub
import redis.asyncio as redis
import time

TIME_OUT = 30
redis_pool: redis.ConnectionPool = None

def timeout_response() -> str:
    return "timed out"

def match_found_response(match_data: dict[str, str]) -> dict[str, str]:
    match_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool, pubsub
    redis_pool = redis.ConnectionPool.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True,
    )
    yield
    await redis_pool.aclose()
    

app = FastAPI(lifespan=lifespan) 

@app.get("/match")
async def get_match(request: Request):
    client: redis.Redis = redis.Redis.from_pool(redis_pool)
    client_id: str = f"{request.client.host}/{request.client.port}"
    await client.zadd(
        'players:queue',
        {client_id: time.time()}
    )

    pubsub: PubSub
    async with client.pubsub() as pubsub:
        channel_name = f'matches:{client_id}'
        await pubsub.subscribe(channel_name)

        while True:
            msg = await pubsub.get_message(timeout=TIME_OUT)
            if msg is not None:
                if msg['data'] != 1:
                    result = match_found_response(msg['data'])
                    break
            else:
                result = timeout_response()
                break
    
    await client.aclose()
    
    return result