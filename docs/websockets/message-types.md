# Message Types

## Server → Client

- `initial-load`
- `match-update`
- `message-update` (legacy alias of `match-update`)
- `gameclock-update`
- `playclock-update`
- `event-update`
- `statistics-update`
- `players-update`
- `ping`

## Client → Server

- `pong`

## Initial Load

The `initial-load` message includes match data, teams, scoreboard, players, events, clocks, and statistics.

Payload shape:

```json
{
  "type": "initial-load",
  "data": {
    "match": { ... },
    "match_data": { ... },
    "teams_data": { ... },
    "scoreboard_data": { ... },
    "players": [ ... ],
    "events": [ ... ],
    "gameclock": { ... },
    "playclock": { ... },
    "statistics": { ... },
    "server_time_ms": 1737974401234
  }
}
```

## Match Updates

`match-update` is used for match, matchdata, scoreboard, and combined updates. The handler may send either the trigger data payload or a fully fetched payload depending on cache availability.

## Clocks

Clock messages are `gameclock-update` and `playclock-update` and are dispatched to subscribed clients by match ID.
