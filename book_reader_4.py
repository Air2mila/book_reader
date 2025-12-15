import os
import json
import uuid
import asyncio  # Libreria core per async
import aiofiles
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
DB_FILE = "session_db.json"
STATIC_FOLDER = os.path.join(os.getcwd(), 'static')

# --- CONFIGURAZIONE ---
# Assicurati che l'URL ngrok sia aggiornato e senza slash finale
BASE_URL = "https://87224285fcde.ngrok-free.app"
AUDIO_URL = f"{BASE_URL}/static/lettura_completa.mp3"

# --- FUNZIONI DI UTILITÀ PER IL FILE ---

async def load_data_async():
    """Carica i dati dal file JSON in modo asincrono."""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        async with aiofiles.open(DB_FILE, mode='r', encoding='utf-8') as f:
            contents = await f.read()
            return json.loads(contents) if contents else {}
    except (json.JSONDecodeError, Exception) as e:
        print(f"Errore caricamento file: {e}")
        return {}

async def save_data_async(user_id, offset, token):
    """Salva lo stato dell'utente nel file JSON in modo asincrono."""
    # 1. Carichiamo i dati esistenti
    data = await load_data_async()

    # 2. Aggiorniamo i dati dell'utente specifico
    data[user_id] = {
        "offset": offset,
        "token": token
    }

    # 3. Scriviamo il file aggiornato sul disco
    try:
        async with aiofiles.open(DB_FILE, mode='w', encoding='utf-8') as f:
            # Trasformiamo il dizionario in stringa JSON
            json_string = json.dumps(data, indent=4)
            await f.write(json_string)
    except Exception as e:
        print(f"Errore salvataggio file: {e}")

# --- FUNZIONI CORE PER ALEXA ---
async def play_audio(user_id, offset, speech):
    # Generiamo o recuperiamo il token
    db = await load_data_async()
    token = db.get(user_id, {}).get("token", str(uuid.uuid4()))

    # Salviamo subito lo stato prima di far partire l'audio
    await save_data_async(user_id, offset, token)

    return jsonify({
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech},
            "directives": [{
                "type": "AudioPlayer.Play",
                "playBehavior": "REPLACE_ALL",
                "audioItem": {
                    "stream": {
                        "url": AUDIO_URL,
                        "token": token,
                        "offsetInMilliseconds": offset
                    }
                }
            }],
            "shouldEndSession": True
        }
    })


def stop_audio():
    return jsonify({
        "version": "1.0",
        "response": {
            "directives": [{
                "type": "AudioPlayer.Stop"
            }],
            "shouldEndSession": True
        }
    })

# --- ROTTE FLASK ---
@app.route('/alexa', methods=['POST'])
async def alexa_skill():
    data = request.json
    request_type = data['request'].get('type')

    # Recupero ID utente robusto (cerca in session o context)
    user_id = (data.get('session', {}).get('user', {}).get('userId') or
               data.get('context', {}).get('System', {}).get('user', {}).get('userId') or
               "default_user")

    # Carichiamo i dati con await
    db = await load_data_async()
    user_state = db.get(user_id, {"offset": 0, "token": str(uuid.uuid4())})

    # 1. AVVIO (LaunchRequest)
    if request_type == "LaunchRequest":
        # Se ha già un offset, chiediamo se vuole riprendere o ricominciare
        if user_state["offset"] > 0:
            msg = "Bentornato. Vuoi riprendere la lettura da dove eri rimasto?"
            return jsonify({
                "version": "1.0",
                "response": {
                    "outputSpeech": {"type": "PlainText", "text": msg},
                    "shouldEndSession": False
                }
            })
        return await play_audio(user_id, 0, "Inizio la lettura del documento.")

    # 2. GESTIONE INTENT (Pausa, Riprendi, Stop)
    if request_type == "IntentRequest":
        intent_name = data['request']['intent']['name']

        if intent_name == "AMAZON.ResumeIntent" or intent_name == "AMAZON.YesIntent":
            return await play_audio(user_id, user_state["offset"], "Riprendo la lettura.")

        if intent_name == "AMAZON.StartOverIntent" or intent_name == "AMAZON.NoIntent":
            return await play_audio(user_id, 0, "Ricomincio la lettura dall'inizio.")

        if intent_name in ["AMAZON.PauseIntent", "AMAZON.StopIntent"]:
            return stop_audio()

    # 3. AGGIORNAMENTO AUTOMATICO POSIZIONE (Eventi AudioPlayer)
    if request_type.startswith("AudioPlayer."):
        # Quando l'audio avanza o si ferma, Alexa ci invia l'offset
        current_offset = data['request'].get('offsetInMilliseconds', user_state["offset"])
        await save_data_async(user_id, current_offset, user_state["token"])
        return jsonify({})

    return jsonify({})



if __name__ == '__main__':
    # Assicurati che la cartella static esista
    os.makedirs(STATIC_FOLDER, exist_ok=True)
    app.run(port=5000, debug=True)