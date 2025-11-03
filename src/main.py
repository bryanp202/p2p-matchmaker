from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from redis.client import PubSub
import redis.asyncio as redis
import time, os, json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

MATCHMAKING_QUEUE_NAME = "players:queue"
TIME_OUT = 30
redis_pool: redis.ConnectionPool = None

async def timeout_response(client: redis.Redis, client_id: str) -> str:
    await client.zrem(MATCHMAKING_QUEUE_NAME, client_id)
    return {"error": "MATCHMAKING_TIMED_OUT"}

def match_found_response(match_data: str):
    return json.loads(match_data)

async def find_match(client: redis.Redis, pubsub: PubSub, client_id: str):
    while True:
        msg = await pubsub.get_message(timeout=TIME_OUT)
        if msg is not None:
            if msg['data'] != 1:
                return match_found_response(msg['data'])
        else:
            return await timeout_response(client, client_id)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool, pubsub

    redis_pool = redis.ConnectionPool.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    # Clear redis
    temp_redis = redis.Redis.from_pool(redis_pool)
    await temp_redis.flushall()
    await temp_redis.aclose()
    yield
    await redis_pool.aclose()
    

app = FastAPI(lifespan=lifespan) 

@app.get("/match")
async def get_match(request: Request):
    client: redis.Redis = redis.Redis(connection_pool=redis_pool)
    client_id: str = f"{request.client.host}/{request.client.port}"
    await client.zadd(
        MATCHMAKING_QUEUE_NAME,
        {client_id: time.time()}
    )

    pubsub: PubSub
    async with client.pubsub() as pubsub:
        channel_name = f'matches:{client_id}'
        await pubsub.subscribe(channel_name)

        response = await find_match(client, pubsub, client_id)
    
    await client.aclose()
    
    return response