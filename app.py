import os
import asyncio
from threading import Thread
from flask import request, render_template
from modules import create_app, start_background_tasks
from modules.socketio_custom import socketio
from modules.scrap_betbra import start_betbra_scanner

# Criar a aplicação e configuração
app, config = create_app()

@app.route('/calculadora')
def calculadora():
    odd1 = request.args.get('odd1')
    odd2 = request.args.get('odd2')
    odd3 = request.args.get('odd3')
    return render_template("calculadora.html", odd1=odd1, odd2=odd2, odd3=odd3)

def start_loop():
    """Loop isolado para o motor BetBra"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Rodamos o motor turbo (via requests)
    loop.run_until_complete(start_betbra_scanner(app))

def run_all_background_tasks(app, config):
    # 1. Inicia as tarefas padrão (Scraper original + Dólar)
    start_background_tasks(app, config)

    # 2. Inicia o motor turbo BetBra numa Thread separada (Essencial no Render)
    betbra_thread = Thread(target=start_loop, daemon=True)
    betbra_thread.start()
    print("✅ [SISTEMA] Motores sincronizados e prontos para o Render")

if __name__ == '__main__':
    # Porta dinâmica do Render (obrigatório)
    port = int(os.environ.get("PORT", 8001))
    
    # Inicia os motores
    run_all_background_tasks(app, config)
    
    # Roda o Socket.IO com eventlet para aguentar produção
    # Debug=False para ganhar performance no servidor
    socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)