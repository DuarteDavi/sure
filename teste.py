import asyncio
import requests
from modules.socketio_custom import socketio

# ⚠️ Atualizar quando expirar (pegar novo no DevTools)
AUTHORIZATION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsYW5ndWFnZUNvZGUiOiJici1wdCIsImN1cnJlbmN5UmF0ZSI6MSwiY3VycmVuY3lSYXRlZXVyIjoxLCJjdXN0b21lckxpbWl0cyI6W10sImN1c3RvbWVyVHlwZSI6ImFub24iLCJjdXJyZW5jeUNvZGUiOiJCUkwiLCJjdXJyZW5jeUNvZGVBbm9uIjoiIiwiY3VzdG9tZXJJZCI6LTEsImJldHRpbmdWaWV3IjoiRXVyb3BlYW4gVmlldyIsInNvcnRpbmdUeXBlSWQiOjAsImJldHRpbmdMYXlvdXQiOjEsImRpc3BsYXlUeXBlSWQiOjEsInRpbWV6b25lSWQiOjEwLCJhdXRvVGltZVpvbmUiOjEsImxhc3RJbnB1dFN0YWtlIjowLCJldU9kZHNJZCI6IjEiLCJhc2lhbk9kZHNJZCI6IjEiLCJrb3JlYW5PZGRzSWQiOiIxIiwiaW50VGFiRXhwYW5kZWQiOjEsImRvbWFpbklEIjo0MzAyLCJhZ2VudElEIjoxNzYxNjYzMTAsInNpdGVJZCI6MjA0NTQsInNlbGVjdGVkT3B0aW9uSWQiOjAsImN1c3RvbWVyTGV2ZWwiOjAsImJhbGFuY2VQcmlvcml0eSI6MSwiRVBPRW5hYmxlZCI6dHJ1ZSwiaWF0IjoxNzc1NTE4NjUwfQ.fwvCwl6yVonOZq2yRd7u1vUoJphz2O0OmzX88vpVEWQ"
SESSION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjdXN0b21lcklkIjotMSwiZXhwaXJlZERhdGUiOjE3NzU2MDUwNTA2OTgsImlhdCI6MTc3NTUxODY1MH0.hCc5Fp3bzxterQgopZrktiRsmExnqFek1IwHH8ezo4c"

# URL exata do DevTools, sem tocar nos params
URL = (
    "https://prod20454-176166310.fssb.io/api/eventlist/eu/events/v2/1/live/eventUpdates"
    "?isAllMarkets=true"
    "&leagueIds=150%2C931%2C2728%2C3768%2C5694%2C6438%2C323413679582478336%2C198025242244706304%2C792892689913008128"
    "&marketTypeIds=ML39%2CML169%2CML1633%2CML1%2COU249%2COU39%2COU6001%2COU1697%2COU1633%2COU201%2CQA158%2CQA1693%2CML0%2CML1%2COU200%2COU201%2CQA158"
    "&view=european"
    "&hideX25X75Selections=false"
    "&withStartSoonMin=5"
)

HEADERS = {
    "accept": "application/json",
    "accept-language": "pt-BR,pt;q=0.9",
    "authorization": AUTHORIZATION,
    "cookie": f"operatorToken=logout; session={SESSION}; authorization={AUTHORIZATION}",
    "referer": "https://prod20454-176166310.fssb.io/br-pt/spbk?selectedDefaultTab=Live&selectedLiveSport=1&langCode=br-pt&oddsStyleId=1&operatorToken=logout&api=https%3A%2F%2Fbetbra.bet.br%2Fassets%2Ffssb%2Fwhl.js",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-fetch-storage-access": "active",
    "session": SESSION,
    "time-area": "",
    "priority": "u=1, i",
}


def get_eventos():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
        print(f"❌ Status {r.status_code}: {r.text[:200]}")
        return []
    except Exception as e:
        print(f"❌ Erro: {e}")
        return []


def parse_evento(ev):
    try:
        nome_jogo = ev[10]
        liga      = ev[2]
        pais      = ev[7]
        placar    = f"{ev[12][0]} x {ev[12][1]}"
        relogio   = ev[15] or {}
        minuto    = relogio.get("GameTime", 0) // 60

        mercados = []
        for m in (ev[19] or []):
            nome_mercado = m[1]
            selecoes = []
            for sel in (m[7] or []):
                suspensa = sel[3]
                if suspensa:
                    continue
                nome_sel = sel[1].get("BR-PT", "?") if isinstance(sel[1], dict) else str(sel[1])
                odd      = sel[4]
                selecoes.append({"nome": nome_sel, "odd": odd})

            if selecoes:
                mercados.append({"mercado": nome_mercado, "selecoes": selecoes})

        return {
            "id":       ev[0],
            "jogo":     nome_jogo,
            "liga":     liga,
            "pais":     pais,
            "placar":   placar,
            "minuto":   minuto,
            "mercados": mercados,
        }
    except Exception as e:
        print(f"⚠️ Erro ao parsear evento: {e}")
        return None


async def start_betbra_scanner(app):
    print("🚀 [BETBRA LIVE] Scanner iniciado...")
    while True:
        eventos = get_eventos()
        print(f"📡 {len(eventos)} eventos ao vivo")

        for ev_raw in eventos:
            evento = parse_evento(ev_raw)
            if evento and evento["mercados"]:
                socketio.emit("evento_ao_vivo", evento)

        await asyncio.sleep(10)