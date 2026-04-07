import requests

AUTHORIZATION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsYW5ndWFnZUNvZGUiOiJici1wdCIsImN1cnJlbmN5UmF0ZSI6MSwiY3VycmVuY3lSYXRlZXVyIjoxLCJjdXN0b21lckxpbWl0cyI6W10sImN1c3RvbWVyVHlwZSI6ImFub24iLCJjdXJyZW5jeUNvZGUiOiJCUkwiLCJjdXJyZW5jeUNvZGVBbm9uIjoiIiwiY3VzdG9tZXJJZCI6LTEsImJldHRpbmdWaWV3IjoiRXVyb3BlYW4gVmlldyIsInNvcnRpbmdUeXBlSWQiOjAsImJldHRpbmdMYXlvdXQiOjEsImRpc3BsYXlUeXBlSWQiOjEsInRpbWV6b25lSWQiOjEwLCJhdXRvVGltZVpvbmUiOjEsImxhc3RJbnB1dFN0YWtlIjowLCJldU9kZHNJZCI6IjEiLCJhc2lhbk9kZHNJZCI6IjEiLCJrb3JlYW5PZGRzSWQiOiIxIiwiaW50VGFiRXhwYW5kZWQiOjEsImRvbWFpbklEIjo0MzAyLCJhZ2VudElEIjoxNzYxNjYzMTAsInNpdGVJZCI6MjA0NTQsInNlbGVjdGVkT3B0aW9uSWQiOjAsImN1c3RvbWVyTGV2ZWwiOjAsImJhbGFuY2VQcmlvcml0eSI6MSwiRVBPRW5hYmxlZCI6dHJ1ZSwiaWF0IjoxNzc1NTE4NjUwfQ.fwvCwl6yVonOZq2yRd7u1vUoJphz2O0OmzX88vpVEWQ"
SESSION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjdXN0b21lcklkIjotMSwiZXhwaXJlZERhdGUiOjE3NzU2MDUwNTA2OTgsImlhdCI6MTc3NTUxODY1MH0.hCc5Fp3bzxterQgopZrktiRsmExnqFek1IwHH8ezo4c"

URL = (
    "https://prod20454-176166310.fssb.io/api/eventlist/eu/events/v2/1/live/eventUpdates"
    "?isAllMarkets=true"
    "&leagueIds=150%2C931%2C2728%2C3768%2C5694%2C6438%2C323413679582478336%2C198025242244706304%2C792892689913008128"
    "&marketTypeIds=ML39%2CML169%2CML1633%2CML1%2COU249%2COU39%2COU6001%2COU1697%2COU1633%2COU201%2CQA158%2CQA1693%2CML0%2CML1%2COU200%2COU201%2CQA158"
    "&view=european&hideX25X75Selections=false&withStartSoonMin=5"
)

HEADERS = {
    "accept": "application/json",
    "authorization": AUTHORIZATION,
    "cookie": f"operatorToken=logout; session={SESSION}; authorization={AUTHORIZATION}",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "session": SESSION,
    "time-area": "",
}

r = requests.get(URL, headers=HEADERS, timeout=15)
print(f"Status: {r.status_code}")

eventos = r.json().get("data", [])
print(f"Total de eventos: {len(eventos)}")

for ev in eventos:
    nome = ev[10]
    placar = f"{ev[12][0]} x {ev[12][1]}"
    minuto = (ev[15] or {}).get("GameTime", 0) // 60

    # pega só o 1X2
    mercado_1x2 = next((m for m in (ev[19] or []) if "1X2" in m[1] or "1x2" in m[1].lower()), None)
    odds = []
    if mercado_1x2:
        for sel in (mercado_1x2[7] or []):
            if not sel[3]:  # não suspensa
                odds.append(f"{sel[1].get('BR-PT','?')}: {sel[4]}")

    print(f"  {minuto}' | {nome} [{placar}] → {' | '.join(odds)}")