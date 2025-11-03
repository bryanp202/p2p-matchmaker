import redis, time, random, json, os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"

SLEEP_TIME_SECONDS = 30
MATCHMAKING_QUEUE_NAME = "players:queue"

def make_match(redis_client: redis.Redis, players: list[str]):
    player1 = players[0]
    player2 = players[1]
    host_index = random.randint(0, 1)
    
    player1_match_data = {
        "local_is_host": host_index == 0,
        "self": player1,
        "peer": player2,
    }
    player2_match_data = {
        "local_is_host": host_index == 1,
        "self": player2,
        "peer": player1,
    }

    redis_client.publish(f"matches:{player1}", json.dumps(player1_match_data))
    redis_client.publish(f"matches:{player2}", json.dumps(player2_match_data))
# End

def match_players(redis_client: redis.Redis):
    players_in_queue = redis_client.zcard(MATCHMAKING_QUEUE_NAME)
    while players_in_queue >= 2:
        players = redis_client.zrange(MATCHMAKING_QUEUE_NAME, 0, 1)
        redis_client.zremrangebyrank(MATCHMAKING_QUEUE_NAME, 0, 1)
        make_match(redis_client, players)
        players_in_queue -= 2
# End
    
def run():
    redis_client: redis.Redis = redis.Redis.from_url(
        REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    while True:
        match_players(redis_client)
        time.sleep(SLEEP_TIME_SECONDS)
# End

run()
