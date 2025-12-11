
# requirements:
# pip install flask aiohttp

import os
import json
import asyncio
import threading
from typing import Optional

from flask import Flask, request, jsonify
import aiohttp

# ==========================
# Config
# ==========================
ALEXA_SKILL_ENDPOINT = "https://your-skill-endpoint.com"
AUTH_TOKEN = "Bearer YOUR_AUTH_TOKEN"
STATE_FILE = "stream_state.json"

# Testo di esempio (puoi sostituire con input dinamico)
TESTO = """
Questo è il primo messaggio.
Questo è il secondo messaggio.
E infine il terzo messaggio.
"""

FRASI = [riga.strip() for riga in TESTO.split("\n") if riga.strip()]

# ==========================
# Persistenza stato
# ==========================
def salva_stato(indice: int):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"indice": indice}, f, ensure_ascii=False)

def carica_stato() -> int:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return int(json.load(f).get("indice", 0))
        except Exception:
            return 0
    return 0

# ==========================
# Streaming asincrono
# ==========================
async def invia_a_alexa(session: aiohttp.ClientSession, frase: str) -> str:
    payload = {"message": frase}
    headers = {
        "Content-Type": "application/json",
        "Authorization": AUTH_TOKEN
    }
    async with session.post(ALEXA_SKILL_ENDPOINT, json=payload, headers=headers, timeout=30) as resp:
        text = await resp.text()
        if resp.status >= 400:
            raise RuntimeError(f"HTTP {resp.status}: {text}")
        return text

class StreamingController:
    """
    Gestisce:
      - indice corrente
      - task stream in esecuzione
      - stop "soft" (si ferma tra un invio e l'altro)
      - persistenza indice
      - sincronizzazione
    """
    def __init__(self, frasi: list[str]):
        self.frasi = frasi
        self._indice: int = carica_stato()
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def indice(self) -> int:
        return self._indice

    async def _stream(self):
        try:
            async with aiohttp.ClientSession() as session:
                i = self._indice
                while i < len(self.frasi) and not self._stop_event.is_set():
                    frase = self.frasi[i]
                    try:
                        risposta = await invia_a_alexa(session, frase)
                        print(f"[STREAM] Inviato: {frase} -> Risposta: {risposta}")
                    except Exception as e:
                        print(f"[STREAM][ERRORE] {e}. Riprovo tra 1s...")
                        # backoff semplice
                        await asyncio.sleep(1)
                        continue

                    i += 1
                    self._indice = i
                    salva_stato(self._indice)
                    # Piccola pausa cooperativa per gesti di stop in arrivo
                    await asyncio.sleep(0)

        finally:
            # Al termine, azzera il task
            async with self._lock:
                self._task = None
                self._stop_event.clear()

    async def start(self, from_index: int = 0) -> str:
        """
        Avvia (o riavvia) lo streaming a partire da from_index.
        Se c'è già uno streaming attivo, lo ferma e ne avvia uno nuovo.
        """
        async with self._lock:
            # stop eventuale stream in corso
            if self._task and not self._task.done():
                self._stop_event.set()
                try:
                    await asyncio.wait_for(self._task, timeout=5)
                except asyncio.TimeoutError:
                    # Lasciamo che il task termini da solo
                    pass

            # reset stato
            self._indice = max(0, min(from_index, len(self.frasi)))
            salva_stato(self._indice)
            self._stop_event.clear()
            self._task = asyncio.create_task(self._stream())
            return f"Streaming avviato dal punto {self._indice}"

    async def continue_(self) -> str:
        """
        Riprende dallo stato salvato (self._indice).
        Se già attivo, non fa nulla.
        """
        async with self._lock:
            if self._task and not self._task.done():
                return "Streaming già in corso"
            if self._indice >= len(self.frasi):
                return "Hai già raggiunto la fine del testo"
            self._stop_event.clear()
            self._task = asyncio.create_task(self._stream())
            return f"Streaming ripreso dal punto {self._indice}"

    async def stop(self) -> str:
        """
        Imposta stop, salva stato e attende la chiusura "soft".
        """
        async with self._lock:
            if not self._task or self._task.done():
                salva_stato(self._indice)
                return f"Nessuno streaming attivo. Stato salvato al punto {self._indice}"
            self._stop_event.set()

        # Rilasciato il lock, aspetta che il task termini
        try:
            await asyncio.wait_for(self._task, timeout=5)
        except asyncio.TimeoutError:
            pass

        salva_stato(self._indice)
        return f"Streaming interrotto e stato salvato al punto {self._indice}"

# ==========================
# Event loop in background per Flask
# ==========================
app = Flask(__name__)
controller = StreamingController(FRASI)

# Avviamo un event loop asyncio in un thread dedicato,
# così possiamo chiamare funzioni async da Flask (che è sync)
loop = asyncio.new_event_loop()

def _run_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_run_loop, args=(loop,), daemon=True).start()

def run_async(coro):
    """
    Utility per eseguire una coroutine async dentro l'event loop di background
    e attendere sincronicamente il risultato lato Flask.
    """
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    return fut.result(timeout=15)

# ==========================
# Endpoint Alexa
# ==========================
@app.route("/alexa", methods=["POST"])
def handle_alexa():
    """
    Esempio di payload:
    {
      "intent": "StartIntent",            # oppure "StopIntent" | "ContinueIntent"
      "startFrom": 0                      # opzionale, per StartIntent
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    intent = data.get("intent")

    if intent == "StartIntent":
        start_from = data.get("startFrom", 0)
        msg = run_async(controller.start(from_index=int(start_from)))
        return jsonify({"response": msg, "indice": controller.indice}), 200

    if intent == "StopIntent":
        msg = run_async(controller.stop())
        return jsonify({"response": msg, "indice": controller.indice}), 200

    if intent == "ContinueIntent":
        msg = run_async(controller.continue_())
        return jsonify({"response": msg, "indice": controller.indice}), 200

    return jsonify({"error": "Comando non riconosciuto"}), 400

# ==========================
# Avvio Flask
# ==========================
if __name__ == "__main__":
    # Nota: per produzione usa un WSGI server (gunicorn/uvicorn+ASGI bridge) e HTTPS.
    app.run(host="0.0.0.0", port=5000, debug=True)

