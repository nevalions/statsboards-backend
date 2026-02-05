# Troubleshooting

## Client Not Receiving Updates

Check:

- Listener subscriptions for expected channels
- Cache invalidation and fetch logic
- Match subscriptions contain the client_id

## Stale Connections

The connection manager cleans stale connections after 90s of inactivity. Ensure client responds to `ping` with `pong`.

## JSON Decode Errors

Trigger payloads must be valid JSON. Check trigger functions for malformed payloads.
