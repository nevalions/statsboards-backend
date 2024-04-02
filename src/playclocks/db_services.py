import time
import asyncio

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select

from src.core.models import BaseServiceDB, PlayClockDB
from .schemas import PlayClockSchemaCreate, PlayClockSchemaUpdate


class ClockManager:
    def __init__(self):
        self.active_playclock_matches = {}

    async def start_clock(self, match_id):
        if match_id not in self.active_playclock_matches:
            self.active_playclock_matches[match_id] = asyncio.Queue()

    async def end_clock(self, match_id):
        if match_id in self.active_playclock_matches:
            del self.active_playclock_matches[match_id]

    async def update_queue_clock(self, match_id, message):
        if match_id in self.active_playclock_matches:
            queue = self.active_playclock_matches[match_id]
            await queue.put(message)


class PlayClockServiceDB(BaseServiceDB):
    def __init__(self, database):
        super().__init__(database, PlayClockDB)
        self.clock_manager = ClockManager()
        # self.match_manager = MatchDataManager()
        # self._running_tasks = {}

    async def create_playclock(self, playclock: PlayClockSchemaCreate):
        async with self.db.async_session() as session:
            try:
                playclock_result = PlayClockDB(
                    playclock=playclock.playclock,
                    playclock_status=playclock.playclock_status,
                    match_id=playclock.match_id,
                )

                is_exist = await self.get_playclock_by_match_id(playclock.match_id)
                if is_exist:
                    return playclock_result

                session.add(playclock_result)
                await session.commit()
                await session.refresh(playclock_result)

                return playclock_result
            except Exception as ex:
                print(ex)
                raise HTTPException(
                    status_code=409,
                    detail=f"While creating playclock "
                           f"for match id({playclock.match_id})"
                           f"returned some error",
                )

    async def enable_match_data_clock_queues(
            self,
            item_id: int,
    ):

        playclock = await self.get_by_id(item_id)

        if not playclock:
            raise ValueError(f"Playclock {item_id} not found")

        active_clock_matches = self.clock_manager.active_playclock_matches

        if item_id not in active_clock_matches:
            await self.clock_manager.start_clock(item_id)
        match_queue = active_clock_matches[item_id]
        await match_queue.put(playclock)

        return match_queue

    async def update_playclock(
            self,
            item_id: int,
            item: PlayClockSchemaUpdate,
            **kwargs,
    ):
        updated_ = await super().update(
            item_id,
            item,
            **kwargs,
        )
        await self.trigger_update_playclock(item_id)
        print(updated_.__dict__)
        return updated_

    async def get_playclock_status(
            self,
            item_id: int,
    ):
        playclock = await self.get_by_id(item_id)
        if playclock:
            return playclock.playclock_status
        else:
            return None

    async def get_playclock_by_match_id(self, match_id: int):
        async with self.db.async_session() as session:
            result = await session.scalars(
                select(PlayClockDB).where(PlayClockDB.match_id == match_id)
            )
            if result:
                print(result.__dict__)
                playclock = result.one_or_none()
                if playclock:
                    return playclock

    async def decrement_playclock(
            self,
            background_tasks: BackgroundTasks,
            match_data_id: int,
    ):
        # Access the queue for the specific match directly
        if match_data_id in self.clock_manager.active_playclock_matches:
            # print(match_data_id)
            background_tasks.add_task(
                self.loop_decrement_playclock,
                match_data_id,
            )
        else:
            print(f"No active match playclock found with id: {match_data_id}")

    async def loop_decrement_playclock(self, playclock_id):
        next_time = time.monotonic()
        while True:
            next_time += 1
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

            # start_time = time.time()
            playclock_status = await self.get_playclock_status(playclock_id)
            print(playclock_status)
            if playclock_status != "running":
                break

            updated_playclock = await self.decrement_playclock_one_second(playclock_id)
            print(updated_playclock)

            if updated_playclock == 0:
                await self.update(
                    playclock_id,
                    PlayClockSchemaUpdate(
                        playclock_status="stopping",
                        playclock=0,
                    ),
                )

                # await self.trigger_update_match_clock(playclock_id, "play")
                await asyncio.sleep(2)

                playclock = await self.update(
                    playclock_id,
                    PlayClockSchemaUpdate(
                        playclock=None,
                        playclock_status="stopped",
                    ),
                )

            else:
                playclock = await self.update(
                    playclock_id, PlayClockSchemaUpdate(playclock=updated_playclock)
                )

            await self.clock_manager.update_queue_clock(
                playclock_id,
                playclock,
            )

            # await asyncio.sleep(1)
            # exec_time = time.time() - start_time
            # await asyncio.sleep(max(1 - exec_time, 0))

        return await self.get_by_id(playclock_id)

    async def decrement_playclock_one_second(
            self,
            item_id: int,
    ):
        print(f"Decrementing playclock for {item_id}")
        result = await self.get_by_id(item_id)
        if result:
            updated_playclock = result.playclock

            if updated_playclock and updated_playclock > 0:
                updated_playclock -= 1
                return updated_playclock

            else:
                await self.update(
                    item_id,
                    PlayClockSchemaUpdate(
                        playclock_status="stopped",
                    ),
                )
                return 0
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Playclock id:{item_id} not found",
            )

    async def trigger_update_playclock(
            self,
            playclock_id: int,
    ):
        playclock = await self.get_by_id(playclock_id)

        active_clock_matches = self.clock_manager.active_playclock_matches

        if playclock_id in active_clock_matches:
            matchdata_clock_queue = active_clock_matches[playclock_id]
            await matchdata_clock_queue.put(playclock)
        else:
            print(f"No active playclock found with id: {playclock_id}")

    # async def get_gameclock_status(
    #     self,
    #     item_id: int,
    # ):
    #     gameclock = await self.get_by_id(item_id)
    #     if gameclock:
    #         return gameclock.gameclock_status
    #     else:
    #         return None

    # async def loop_decrement_gameclock(self, match_data_id: int):
    #     # Initialize the game clock from the database
    #     gameclock = (await self.get_by_id(match_data_id)).gameclock
    #
    #     while True:
    #         start_time = time.time()
    #         gameclock_status = await self.get_gameclock_status(match_data_id)
    #         if gameclock_status != "running":
    #             await self.update(
    #                 match_data_id,
    #                 PlayClockSchemaUpdate(gameclock=gameclock),
    #             )
    #             break
    #
    #         # Decrement gameclock in memory
    #         gameclock = max(gameclock - 1, 0)
    #
    #         # if gameclock % 60 == 0:  # Update database every 60 seconds
    #         await self.update(
    #             match_data_id,
    #             MatchDataSchemaUpdate(gameclock=gameclock),
    #         )
    #
    #         # Send updated gameclock to SSE
    #         await self.clock_manager.update_queue_clock(
    #             match_data_id,
    #             {"gameclock": gameclock, "gameclock_status": "running"},
    #             "game",
    #         )
    #
    #         exec_time = time.time() - start_time
    #         sleep_time = max(1 - exec_time, 0)
    #         await asyncio.sleep(sleep_time)
    #
    #     return await self.get_by_id(match_data_id)

    # async def decrement_gameclock(
    #     self,
    #     background_tasks: BackgroundTasks,
    #     match_data_id: int,
    # ):
    #     # Access the queue for the specific match directly
    #     if match_data_id in self.clock_manager.active_gameclock_matches:
    #         background_tasks.add_task(
    #             self.loop_decrement_gameclock,
    #             match_data_id,
    #         )
    #     else:
    #         print(f"No active match found with id: {match_data_id}")

    # async def event_generator_get_match_clock(
    #     self,
    #     match_id: int,
    #     clock_type: str,
    # ):
    #     active_clock_matches = (
    #         self.clock_manager.active_gameclock_matches
    #         if clock_type == "game"
    #         else self.clock_manager.active_playclock_matches
    #     )
    #
    #     if clock_type == "game" and match_id not in active_clock_matches:
    #         print(f"Queue not found for MatchData ID:{match_id}")
    #         start_game = "in-progress"
    #         await self.update(match_id, MatchDataSchemaUpdate(game_status=start_game))
    #         await self.enable_match_data_clock_queues(match_id, clock_type)
    #
    #         return
    #
    #     # else:
    #     await self.enable_match_data_clock_queues(match_id, clock_type)
    #
    #     try:
    #         while match_id in active_clock_matches:
    #             print(f"Match {match_id} {clock_type} clock is active")
    #             message = await active_clock_matches[match_id].get()
    #             message_dict = self.to_dict(message)
    #
    #             data = {
    #                 "type": clock_type + "Clock",
    #             }
    #             for field in [f"{clock_type}clock", f"{clock_type}clock_status"]:
    #                 data[field] = message_dict[field]
    #
    #             json_data = json.dumps(data, default=self.default_serializer)
    #
    #             yield f"data: {json_data}\n\n"
    #
    #             print(f"Yielded data: {json_data}")
    #
    #             if (
    #                 clock_type == "game"
    #                 and message_dict.get("game_status") == "stopped"
    #             ):
    #                 await self.clock_manager.end_clock(
    #                     match_id,
    #                     "game",
    #                 )
    #                 break
    #
    #         print(f"Match {match_id} {clock_type.capitalize()} Clock stopped")
    #     except asyncio.CancelledError:
    #         pass

    # async def trigger_update_match_data(self, match_data_id):
    #     match_data = await self.get_by_id(match_data_id)
    #     print(match_data)
    #     if match_data_id not in self.match_manager.active_matchdata_updates:
    #         print(f"Queue not found for MatchData ID:{match_data_id}")
    #         await self.match_manager.enable_match_data_update_queue(match_data_id)
    #
    #     await self.match_manager.update_queue_match_data(match_data_id, match_data)

    # async def event_generator_get_match_data(self, match_data_id: int):
    #     await self.match_manager.enable_match_data_update_queue(match_data_id)
    #     try:
    #         while match_data_id in self.match_manager.active_matchdata_updates:
    #             print(f"Match {match_data_id} is active for updates")
    #             message = await self.match_manager.active_matchdata_updates[
    #                 match_data_id
    #             ].get()
    #             message_dict = self.to_dict(message)
    #
    #             # Create a new dictionary with 'type' and 'data' properties
    #             data = {
    #                 "type": "matchData",
    #                 "data": message_dict,
    #             }
    #
    #             json_data = json.dumps(
    #                 data,
    #                 default=self.default_serializer,
    #             )
    #             print(f"Match data {json_data} sent")
    #             yield f"data: {json_data}\n\n"
    #
    #         print(f"Match data {match_data_id} stopped updates")
    #     except asyncio.CancelledError:
    #         print("Cancelled")
    #         pass

    # async def trigger_update_match_clock(
    #     self,
    #     match_data_id: int,
    #     clock_type: str,
    # ):
    #     match_data = await self.get_by_id(match_data_id)
    #
    #     active_clock_matches = (
    #         self.clock_manager.active_gameclock_matches
    #         if clock_type == "game"
    #         else self.clock_manager.active_playclock_matches
    #     )
    #
    #     if match_data_id in active_clock_matches:
    #         matchdata_clock_queue = active_clock_matches[match_data_id]
    #         await matchdata_clock_queue.put(match_data)
    #     else:
    #         print(f"No active {clock_type}clock match found with id: {match_data_id}")
