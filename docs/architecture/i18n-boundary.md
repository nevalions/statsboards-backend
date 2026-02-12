# I18n Boundary (Scoreboard)

## Decision

- Frontend owns scoreboard display lexicon and runtime language switching.
- Backend returns stable semantic keys/codes and configuration flags.
- Backend localization is limited to API/server messages when required.

## Why

- Avoid duplicate dictionaries across backend and frontend.
- Prevent translation drift between API payloads and UI labels.
- Keep backend contracts language-neutral and stable.

## Backend Contract Rules

- Use enums/codes for behavior and mode fields (for example `direction`, `on_stop_behavior`, `period_mode`).
- For custom period labels, use machine-friendly semantic keys instead of display text.
- Do not introduce translated scoreboard display strings in backend responses.

## Examples

Example sport scoreboard preset payload from backend:

```json
{
  "id": 4,
  "title": "football.default",
  "direction": "down",
  "on_stop_behavior": "hold",
  "period_mode": "custom",
  "period_labels_json": ["period.q1", "period.q2", "period.q3", "period.q4"],
  "is_downdistance": true
}
```

Frontend mapping example (en/ru):

```typescript
const periodLabelDict = {
  en: {
    "period.q1": "Q1",
    "period.q2": "Q2",
    "period.q3": "Q3",
    "period.q4": "Q4",
  },
  ru: {
    "period.q1": "1-я четверть",
    "period.q2": "2-я четверть",
    "period.q3": "3-я четверть",
    "period.q4": "4-я четверть",
  },
};
```

## Follow-up

- If localized backend error messages are required, implement them separately and keep scoreboard payloads language-neutral.
