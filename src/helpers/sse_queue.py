import asyncio
import json
from datetime import datetime

from src.core.models import BaseServiceDB


class MatchEventQueue(BaseServiceDB):
    def __init__(self, database, model):
        super().__init__(database, model)
        self.update_queue_match_data = asyncio.Queue()
        self.update_queue_match_data_playclock = asyncio.Queue()
        self.update_queue_match_data_gameclock = asyncio.Queue()

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

    async def trigger_update_match_data(self, match_data_id):
        match_data = await self.get_by_id(match_data_id)
        await self.update_queue_match_data.put({"match_data": self.to_dict(match_data)})

    async def trigger_update_match_data_playclock(self, match_data_id):
        match_data = await self.get_by_id(match_data_id)
        await self.update_queue_match_data_playclock.put(
            {"match_data": self.to_dict(match_data)}
        )

    async def trigger_update_match_data_gameclock(self, match_data_id):
        match_data = await self.get_by_id(match_data_id)
        print(match_data)
        await self.update_queue_match_data_gameclock.put(
            {"match_data": self.to_dict(match_data)}
        )

    async def trigger_get_match_data_gameclock(self):
        data = await self.update_queue_match_data_gameclock.get()
        return {
            "gameclock_data": {
                "gameclock": data["match_data"]["gameclock"],
                "gameclock_status": data["match_data"]["gameclock_status"],
            }
        }


#
# # Usage example:
# match1_event_queue = MatchEventQueue()
# match2_event_queue = MatchEventQueue()
#
# # Trigger events for match 1
# await match1_event_queue.trigger_update_match_data(match1_id)
# await match1_event_queue.trigger_update_match_data_playclock(match1_id)
# await match1_event_queue.trigger_update_match_data_gameclock(match1_id)
#
# # Trigger events for match 2
# await match2_event_queue.trigger_update_match_data(match2_id)
# await match2_event_queue.trigger_update_match_data_playclock(match2_id)
# await match2_event_queue.trigger_update_match_data_gameclock(match2_id)
