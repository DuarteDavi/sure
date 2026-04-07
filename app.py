import asyncio
from threading import Thread
from flask import request, render_template
from modules import create_app, start_background_tasks
from modules.socketio_custom import socketio

# Importamos o nosso motor novo
from modules.scrap_betbra import start_betbra_scanner

app, config = create_app()

# Rota da calculadora (mantida a original dele)
@app.route('/calculadora')
def calculadora():
    odd1 = request.args.get('odd1')
    odd2 = request.args.get('odd2')
    odd3 = request.args.get('odd3')
    return render_template("calculadora.html", odd1=odd1, odd2=odd2, odd3=odd3)

# Função para iniciar os processos em segundo plano
def run_all_background_tasks(app, config):
    # 1. Inicia as tarefas padrão do sistema dele (Scraper Playwright + Dólar)
    start_background_tasks(app, config)

    # 2. Inicia o nosso motor turbo da BetBra numa Thread separada
    def start_loop():
        # Cria um novo loop de eventos para esta thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(start_betbra_scanner(app))

    betbra_thread = Thread(target=start_loop, daemon=True)
    betbra_thread.start()
    print("✅ [SISTEMA] Motores sincronizados: Playwright e BetBra API")

if __name__ == '__main__':
    # Dá a partida nos motores
    run_all_background_tasks(app, config)
    
    # Inicia o servidor Socket.IO
    # Debug=True para ver erros, use_reloader=False para não duplicar os motores
    socketio.run(app, host="0.0.0.0", port=8001, debug=True, use_reloader=False)