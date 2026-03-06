# Tamagotchi Tracker: Local Run Checklist

## 1. Prepare `.env`
1. Copy `.env.example` to `.env`.
2. Fill real values for:
`BOT_TOKEN`, `JWT_SECRET_KEY`, `INTERNAL_API_TOKEN`.
3. Keep `INTERNAL_API_TOKEN` identical for API and bot (both read from root `.env` in `compose.yaml`).

Quick token generation example:
```bash
openssl rand -hex 32
```

## 2. Start services
```bash
docker compose -f compose.yaml down
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml ps
```

## 3. Basic checks
1. API root should open: `http://localhost:8080/`.
2. Internal endpoint without token must be denied:
```bash
curl -i -X POST http://localhost:8080/v1/rewards/add-vpn-hours \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"hours":24,"reason":"test"}'
```
Expected: `401` or `503`.

3. Internal endpoint with token should pass auth layer:
```bash
curl -i -X POST http://localhost:8080/v1/rewards/add-vpn-hours \
  -H "Content-Type: application/json" \
  -H "X-Internal-Token: <INTERNAL_API_TOKEN>" \
  -d '{"user_id":1,"hours":24,"reason":"test"}'
```
Expected: not `401` and not `503` (may still fail by business logic if user data is missing).

## 4. Important notes
1. `TON` verification endpoints are intentionally disabled (`501`) until secure on-chain verification is implemented.
2. Production should use strict CORS and HTTPS.
