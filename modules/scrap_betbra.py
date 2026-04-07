import asyncio
import requests
from modules.socketio_custom import socketio

# ⚠️ Atualizar quando expirar (pegar novo no DevTools)
AUTHORIZATION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsYW5ndWFnZUNvZGUiOiJici1wdCIsImN1cnJlbmN5UmF0ZSI6MSwiY3VycmVuY3lSYXRlZXVyIjoxLCJjdXN0b21lckxpbWl0cyI6W10sImN1c3RvbWVyVHlwZSI6ImFub24iLCJjdXJyZW5jeUNvZGUiOiJCUkwiLCJjdXJyZW5jeUNvZGVBbm9uIjoiIiwiY3VzdG9tZXJJZCI6LTEsImJldHRpbmdWaWV3IjoiRXVyb3BlYW4gVmlldyIsInNvcnRpbmdUeXBlSWQiOjAsImJldHRpbmdMYXlvdXQiOjEsImRpc3BsYXlUeXBlSWQiOjEsInRpbWV6b25lSWQiOjEwLCJhdXRvVGltZVpvbmUiOjEsImxhc3RJbnB1dFN0YWtlIjowLCJldU9kZHNJZCI6IjEiLCJhc2lhbk9kZHNJZCI6IjEiLCJrb3JlYW5PZGRzSWQiOiIxIiwiaW50VGFiRXhwYW5kZWQiOjEsImRvbWFpbklEIjo0MzAyLCJhZ2VudElEIjoxNzYxNjYzMTAsInNpdGVJZCI6MjA0NTQsInNlbGVjdGVkT3B0aW9uSWQiOjAsImN1c3RvbWVyTGV2ZWwiOjAsImJhbGFuY2VQcmlvcml0eSI6MSwiRVBPRW5hYmxlZCI6dHJ1ZSwiaWF0IjoxNzc1NTE4NjUwfQ.fwvCwl6yVonOZq2yRd7u1vUoJphz2O0OmzX88vpVEWQ"
SESSION = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjdXN0b21lcklkIjotMSwiZXhwaXJlZERhdGUiOjE3NzU2MDUwNTA2OTgsImlhdCI6MTc3NTUxODY1MH0.hCc5Fp3bzxterQgopZrktiRsmExnqFek1IwHH8ezo4c"

# URL exata do DevTools — não usar params= pois re-encoda e quebra a requisição
URL = (
    "https://prod20454-176166310.fssb.io/api/eventlist/eu/events/v2/1/live/eventUpdates"
    "?isAllMarkets=true"
    
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


def get_eventos_ao_vivo():
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
        print(f"❌ Status {r.status_code}: {r.text[:200]}")
        return []
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return []


def parse_evento(ev):
    try:
        times = ev[8]
        if not times or not isinstance(times, list) or len(times) < 2:
            print(f"⏭️ Ignorado: {ev[10]} | ev[8]={ev[8]}")
            return None

        nome_casa = times[0][1].get("BR-PT", "?") if isinstance(times[0][1], dict) else "?"
        nome_fora = times[1][1].get("BR-PT", "?") if isinstance(times[1][1], dict) else "?"

        placar    = ev[12] or ["-", "-"]
        gols_casa = placar[0] if placar[0] is not None else "-"
        gols_fora = placar[1] if placar[1] is not None else "-"

        relogio = ev[15] or {}
        minuto  = relogio.get("GameTime", 0) // 60 if relogio.get("GameTime") else "-"

        # Busca só o mercado 1X2
        mercado_1x2 = None
        # Busca só o mercado 1X2 pelo tipo ML39
        mercado_1x2 = None
        for m in (ev[19] or []):
            if not m or not m[7]:
                continue
            tipo = m[3][0] if m[3] and len(m[3]) > 0 else ""
            if tipo == "ML39":
                mercado_1x2 = m
                break

        if not mercado_1x2:
            return None

        # Extrai Casa, Empate, Fora
        odds = {"Casa": "-", "Empate": "-", "Fora": "-"}
        for sel in mercado_1x2[7]:
            if not sel or sel[3]:  # None ou suspensa
                continue
            posicao = sel[9].get("BR-PT", "") if isinstance(sel[9], dict) else ""
            odd     = sel[4]
            if posicao in odds:
                odds[posicao] = odd

        return {
            "id":      ev[0],
            "jogo":    ev[10],
            "liga":    ev[2],
            "casa":    nome_casa,
            "fora":    nome_fora,
            "placar":  f"{gols_casa} x {gols_fora}",
            "minuto":  minuto,
            "odd_casa":   odds["Casa"],
            "odd_empate": odds["Empate"],
            "odd_fora":   odds["Fora"],
        }
    except Exception as e:
        print(f"⚠️ Erro ao parsear evento: {e}")
        return None


async def start_betbra_scanner(app):
    print("🚀 [BETBRA LIVE] Scanner iniciado...")
    while True:
        eventos = get_eventos_ao_vivo()
        print(f"📡 {len(eventos)} eventos ao vivo")

        emitidos = 0
        for ev_raw in eventos:
            evento = parse_evento(ev_raw)
            if not evento:
                continue

            # Só emite se tiver pelo menos uma odd real
            if evento["odd_casa"] == "-" and evento["odd_empate"] == "-" and evento["odd_fora"] == "-":
                print(f"⏭️ Sem odds: {evento['jogo']}")
                continue

            emitidos += 1
            socketio.emit("nova_surebet_front", {
                "id":  evento["id"],
                "roi": f"{evento['minuto']}'",
                "age": evento["liga"],
                "legs": [
                    {"bookmaker": evento["casa"],  "event": evento["jogo"], "market": "Casa",   "odd": evento["odd_casa"]},
                    {"bookmaker": "Empate",        "event": evento["jogo"], "market": "Empate", "odd": evento["odd_empate"]},
                    {"bookmaker": evento["fora"],  "event": evento["jogo"], "market": "Fora",   "odd": evento["odd_fora"]},
                ]
            })

        print(f"✅ {emitidos} jogos com odds emitidos")
        await asyncio.sleep(10)