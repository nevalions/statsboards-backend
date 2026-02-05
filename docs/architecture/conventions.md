# Conventions and Future Work

## Conventions

- Use service registry for cross-domain access
- Keep routers thin; move logic to services
- Prefer selectinload for relationship loading
- Use shared schema patterns for consistency

## Future Enhancements

- Event-driven architecture where appropriate
- Expanded caching layer
- API rate limiting
- API versioning strategy

## Summary

The system is a layered FastAPI backend with a strong service registry pattern, async data access, and real-time WebSocket flows. The architecture prioritizes maintainability, scalability, and predictable patterns across domains.
