import os
import time
import requests
import yfinance as ticker_data

# Configuración tomada de variables de entorno en Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Símbolo para el Oro (XAU/USD en Yahoo Finance)
SYMBOL = "GC=F"

# Intervalo de revisión en segundos (revisa cada 3 minutos)
CHECK_INTERVAL = 180  

# Variable para evitar duplicar alertas
last_pre_alert = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error enviando mensaje a Telegram: {e}")
        return None

def analyze_market():
    global last_pre_alert
    try:
        # Descargar datos más recientes del mercado
        gold = ticker_data.Ticker(SYMBOL)
        df = gold.history(period="1d", interval="5m")

        if df.empty or len(df) < 2:
            print("Esperando más datos del mercado...")
            return

        current_price = df['Close'].iloc[-1]
        previous_price = df['Close'].iloc[-2]

        # Evaluación de tendencia previa (Pre-Detección)
        potential_signal = None
        if current_price > previous_price * 1.0003:  # Indicio de subida
            potential_signal = "COMPRA 🟢"
        elif current_price < previous_price * 0.9997:  # Indicio de bajada
            potential_signal = "VENTA 🔴"

        # Si detecta posible señal y es distinta a la anterior
        if potential_signal and potential_signal != last_pre_alert:
            
            # 1. ENVIAR PRE-ALERTA DE 5 MINUTOS
            pre_message = (
                f"⏳ *PRE-ALERTA DE SEÑAL (5 MINUTOS)* ⏳\n\n"
                f"📊 *Activo:* XAU/USD (Oro)\n"
                f"👀 *Posible dirección:* {potential_signal}\n"
                f"💵 *Precio actual:* ${current_price:.2f}\n\n"
                f"⚠️ Analizando confirmación... La señal definitiva se enviará en 5 minutos."
            )
            send_telegram_message(pre_message)
            last_pre_alert = potential_signal
            print(f"Pre-alerta enviada: Posible {potential_signal}")

            # 2. ESPERAR 5 MINUTOS (300 SEGUNDOS)
            time.sleep(300)

            # 3. REVALUAR Y ENVIAR SEÑAL DEFINITIVA
            fresh_df = gold.history(period="1d", interval="5m")
            confirm_price = fresh_df['Close'].iloc[-1]

            tp = round(confirm_price * 1.002, 2) if "COMPRA" in potential_signal else round(confirm_price * 0.998, 2)
            sl = round(confirm_price * 0.998, 2) if "COMPRA" in potential_signal else round(confirm_price * 1.002, 2)

            final_message = (
                f"🚨 *SEÑAL CONFIRMADA* 🚨\n\n"
                f"📊 *Activo:* XAU/USD (Oro)\n"
                f"🎯 *Acción:* {potential_signal}\n"
                f"💵 *Precio Entrada:* ${confirm_price:.2f}\n"
                f"🎯 *Take Profit (TP):* ${tp}\n"
                f"🛡️ *Stop Loss (SL):* ${sl}\n\n"
                f"🚀 ¡Tomar entrada según tu gestión de riesgo!"
            )
            send_telegram_message(final_message)
            print(f"Señal final confirmada enviada a ${confirm_price:.2f}")

        else:
            print(f"Mercado estable. Sin patrones nuevos.")

    except Exception as e:
        print(f"Error analizando el mercado: {e}")

if _name_ == "_main_":
    print("Iniciando Bot detector de señales con pre-alerta de 5 minutos...")
    send_telegram_message("🤖 Bot de Señales Iniciado (Con Pre-alerta de 5 min)")

    while True:
        analyze_market()
        time.sleep(CHECK_INTERVAL)
