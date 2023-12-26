import json
from redis import asyncio as aioredis
from datetime import datetime

from src.core.models import MatchDataDB


class MatchEventQueue:
    def __init__(self, model, redis, match_data_id):
        super().__init__()
        self.redis = redis
        self.model = model
        self.match_data_id = match_data_id
        self.pubsub_gameclock_channel = f"match_event_queue_channel:{match_data_id}"
        self.pubsub_gameclock = None

    # async def fetch_and_print_keys(self):
    #     keys = await self.redis.keys("match_event_queue:*")
    #     return list(keys)

    async def put_redis(self, data):
        serialized_data = json.dumps(data, default=self.default_serializer)
        list_key = f"match_event_queue:{self.match_data_id}"

        await self.redis.set(list_key, serialized_data)
        # print(f"Pushed data into Redis list {list_key}")
        #
        # keys = await self.redis.keys("match_event_queue:*")
        # print("Keys in Redis:", keys)

    async def get_redis(self):
        key = f"match_event_queue:{self.match_data_id}"
        # print(f"Checking queue: {key}")
        exists = await self.redis.exists(key)
        # print(f"Queue exists: {exists}")
        if exists:
            data = await self.redis.get(key)
            # print(f"LPOP result: {data}")
            if data:
                return json.loads(data)
        return None

    async def close(self):
        # Close the Redis connection
        await self.redis.close()

    # async def close(self):
    #     # Close the connection when the instance is no longer needed
    #     await self.close_connection()

    async def is_connection_open(self):
        try:
            # Use a simple command to check the connection status
            result = await self.redis.ping()
            return result
        except aioredis.RedisError:
            return False

    async def setup_pubsub_gameclock(self):
        self.pubsub_gameclock = self.redis.pubsub()
        await self.pubsub_gameclock.subscribe(self.pubsub_gameclock_channel)

    async def publish_event(self, data):
        await self.redis.publish(
            self.pubsub_gameclock_channel,
            json.dumps(data, default=self.default_serializer),
        )

    @staticmethod
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, MatchDataDB):
            return MatchEventQueue.to_dict(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def to_dict(model):
        data = {
            column.name: getattr(model, column.name)
            for column in model.__table__.columns
        }
        # Exclude the _sa_instance_state key
        data.pop("_sa_instance_state", None)
        return data
