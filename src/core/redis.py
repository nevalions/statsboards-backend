from redis import asyncio as aioredis

from src.core.models import MatchDataDB
from src.helpers.sse_queue import MatchEventQueue


class RedisService:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url: str = redis_url

    async def create_redis_connection(self):
        try:
            redis_connection = await aioredis.from_url(
                self.redis_url, decode_responses=True
            )
            return redis_connection
        except (aioredis.ConnectionError, OSError, ValueError) as e:
            raise

    async def create_match_event_queue(self, match_data_id) -> MatchEventQueue:
        # Create a new MatchEventQueue instance each time
        redis = await self.create_redis_connection()
        return MatchEventQueue(
            redis=redis, model=MatchDataDB, match_data_id=match_data_id
        )

    async def get_match_event_queue(self, match_data_id, match_data=None):
        # Create a new MatchEventQueue instance
        match_queue = await self.create_match_event_queue(match_data_id)
        # Check if the queue already exists in Redis
        if not await match_queue.get_redis():
            await match_queue.put_redis(match_data)
        return match_queue


# import aioredis
#
# from src.core.models import BaseServiceDB, MatchDataDB
#
#
# class MatchEventQueue:
#     def __init__(self, redis, model, match_data_id):
#         self.redis = redis
#         self.model = model
#         self.match_data_id = match_data_id
#
#     async def put(self, data):
#         await self.redis.lpush(
#             f"match_event_queue:{self.match_data_id}", json.dumps(data)
#         )
#
#     async def get(self):
#         data = await self.redis.lpop(f"match_event_queue:{self.match_data_id}")
#         if data:
#             return json.loads(data)
#         return None
#
#
# class MatchDataServiceDB(BaseServiceDB):
#     def __init__(self, database, redis_url):
#         super().__init__(database, MatchDataDB)
#         self.match_event_queues = {}
#         self.redis_url = redis_url
#
#     # ... (other methods remain unchanged)
#
#     # async def create_redis_connection(self):
#     #     return await aioredis.create_redis_pool(self.redis_url)
#     #
#     # async def create_match_event_queue(self, match_data_id):
#     #     redis = await self.create_redis_connection()
#     #     matchdata_gameclock_queue = MatchEventQueue(
#     #         redis=redis, model=MatchDataDB, match_data_id=match_data_id
#     #     )
#     #     return matchdata_gameclock_queue
#     #
#     # async def get_match_event_queue(self, match_data_id):
#     #     return self.match_event_queues.get(match_data_id)
#     #
#     # async def flush_match_event_queue(self, match_data_id):
#     #     # Remove the queue for this match
#     #     self.match_event_queues.pop(match_data_id, None)
#     #
#     # async def enable_match_data_events_queues(self, item_id: int):
#     #     print(item_id)
#     #     match_data = await self.get_by_id(item_id)
#     #     print(match_data)
#     #
#     #     if match_data:
#     #         # Check if the game_status has changed to "in-progress"
#     #         if match_data.game_status == "in-progress":
#     #             match_data_id = match_data.id
#     #             print(match_data.game_status)
#     #
#     #             # Check if the queue already exists for this match
#     #             if match_data_id not in self.match_event_queues:
#     #                 matchdata_gameclock_queue = await self.create_match_event_queue(
#     #                     match_data_id
#     #                 )
#     #                 # Store the queue for this match
#     #                 self.match_event_queues[match_data_id] = matchdata_gameclock_queue
#     #                 print(self.match_event_queues)
#     #
#     #             match_queue = self.match_event_queues.get(match_data_id)
#     #
#     #             # Check if the queue exists before putting the data
#     #             if match_queue:
#     #                 await match_queue.put({"match_data": self.to_dict(match_data)})
#     #                 print(match_queue)
#     #             else:
#     #                 print("Match not started")
#     #         else:
#     #             print("Match not in progress")
#     #     else:
#     #         print(f"Match data {item_id} not found")
