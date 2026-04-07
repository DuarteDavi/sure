import os
import asyncio
import requests
from modules.socketio_custom import socketio

# Pegamos os tokens das variáveis de ambiente do Render. 
# Se não existirem, usamos esses valores padrão (fallback).
AUTHORIZATION = os.environ.get("BETBRA_AUTH", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
SESSION = os.environ.get("BETBRA_SESSION", "eyJhbGciOiJIUzI1NiIsInR5cCI6...")

# URL da API de eventos ao vivo
URL = (
    "https://prod20454-176166310.fssb.io/api/eventlist/eu/events/v2/1/live/eventUpdates"
    "?isAllMarkets=true"
    "&marketTypeIds=ML39%2CML169%2CML1633%2CML1%2COU249%2COU39%2COU6001%2COU1697%2COU1633%2COU201%2CQA158%2CQA1693%2CML0%2CML1%2COU200%2COU201%2CQA158"
    "&view=european"
    "&hideX25X75Selections=false"
    "&withStartSoonMin=5"
)

def get_headers():
    """Gera os headers dinamicamente usando os tokens atuais"""
    return {
        "accept": "application/json",
        "accept-language": "pt-BR,pt;q=0.9",
        "authorization": AUTHORIZATION,
        "cookie": f"operatorToken=logout; session={SESSION}; authorization={AUTHORIZATION}",
        "referer": "https://betbra.bet.br/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "session": SESSION,
        "priority": "u=1, i",
    }

def get_eventos_ao_vivo():
    try:
        # Usamos os headers atualizados
        r = requests.get(URL, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
        
        # Se der 401 ou 403, avisa que o token caiu
        if r.status_code in [401, 403]:
            print(f"⚠️ [AVISO] Tokens expirados no Render (Status {r.status_code})")
        else:
            print(f"❌ Status {r.status_code}: {r.text[:100]}")
        return []
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return []

def parse_evento(ev):
    """Mapeia os dados do array FSSB"""
    try:
        # ev[8] contém os times
        times = ev[8]
        if not times or len(times) < 2: return None

        nome_casa = times[0][1].get("BR-PT", "Casa") if isinstance(times[0][1], dict) else "Casa"
        nome_fora = times[1][1].get("BR-PT", "Fora") if isinstance(times[1][1], dict) else "Fora"

        # ev[12] placar | ev[15] relógio
        placar = ev[12] or [0, 0]
        relogio = ev[15] or {}
        minuto = relogio.get("GameTime", 0) // 60 if relogio.get("GameTime") else "0"

        # Busca mercado 1X2 (Tipo ML39) no ev[19]
        mercado_1x2 = None
        for m in (ev[19] or []):
            if m and m[3] and m[3][0] == "ML39":
                mercado_1x2 = m
                break

        if not mercado_1x2 or not mercado_1x2[7]: return None

        # Extrai Odds: sel[9] indica a posição (Casa, Empate, Fora), sel[4] é a Odd
        odds = {"Casa": "-", "Empate": "-", "Fora": "-"}
        for sel in mercado_1x2[7]:
            if not sel or sel[3]: continue # sel[3] True significa mercado suspenso
            
            posicao_obj = sel[9].get("BR-PT", "") if isinstance(sel[9], dict) else ""
            odd = sel[4]
            if posicao_obj in odds:
                odds[posicao_obj] = odd

        return {
            "id": ev[0],
            "jogo": ev[10],
            "liga": ev[2],
            "casa": nome_casa,
            "fora": nome_fora,
            "minuto": minuto,
            "odd_casa": odds["Casa"],
            "odd_empate": odds["Empate"],
            "odd_fora": odds["Fora"],
        }
    except Exception as e:
        return None

async def start_betbra_scanner(app):
    print("🚀 [BETBRA LIVE] Scanner em execução...")
    while True:
        eventos = get_eventos_ao_vivo()
        emitidos = 0

        for ev_raw in eventos:
            evento = parse_evento(ev_raw)
            if not evento: continue

            # Validação de odds reais
            if all(o == "-" for o in [evento["odd_casa"], evento["odd_empate"], evento["odd_fora"]]):
                continue

            emitidos += 1
            socketio.emit("nova_surebet_front", {
                "id": evento["id"],
                "roi": f"{evento['minuto']}'",
                "age": evento["liga"],
                "legs": [
                    {"bookmaker": evento["casa"], "event": evento["jogo"], "market": "1", "odd": evento["odd_casa"]},
                    {"bookmaker": "Empate", "event": evento["jogo"], "market": "X", "odd": evento["odd_empate"]},
                    {"bookmaker": evento["fora"], "event": evento["jogo"], "market": "2", "odd": evento["odd_fora"]},
                ]
            })

        print(f"✅ Ciclo concluído: {emitidos} jogos ativos")
        # Delay de 10 segundos para evitar bloqueios por excesso de requests
        await asyncio.sleep(10)