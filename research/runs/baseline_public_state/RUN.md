# Run: baseline_public_state

- Date: 2025-09-28
- Stack: Nginx + Daphne + Channels + Redis
- Endpoint: /api/state (public)
- Host: http://localhost:8080
- Users: 50
- Spawn rate: 5 / second
- Duration: 2 minutes
- Defenses:
  - Nginx API rate-limit: ON
  - DRF throttles: [specify current anon/user settings]
