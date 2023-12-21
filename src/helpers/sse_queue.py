import json
from datetime import datetime


class MatchEventQueue:
    def __init__(self, model, redis, match_data_id):
        super().__init__()
        self.redis = redis
        self.model = model
        self.match_data_id = match_data_id

    async def put(self, data):
        serialized_data = json.dumps(data, default=self.default_serializer)
        await self.redis.lpush(
            f"match_event_queue:{self.match_data_id}",
            serialized_data,
        )

    async def get(self):
        data = await self.redis.lpop(f"match_event_queue:{self.match_data_id}")
        if data:
            return json.loads(data)
        return None

    @staticmethod
    def default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
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
