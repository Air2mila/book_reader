import os
import asyncio
import edge_tts
import docx
import fitz  # PyMuPDF

# === CONFIG ===
'''os.environ['http_proxy'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['HTTP_PROXY'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['https_proxy'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['HTTPS_PROXY'] = "http://proxy.dcl.tetrapak.com:8080"
'''
def estrai_testo_da_cartella(percorso_cartella):
    # 1. Cerca il primo file che termina con .pdf nella cartella
    file_pdf = None
    for file in os.listdir(percorso_cartella):
        if file.lower().endswith(".pdf"):
            file_pdf = os.path.join(percorso_cartella, file)
            print(f"File trovato: {file_pdf}")
            break  # Si ferma al primo file trovato

    if not file_pdf:
        return "Nessun file PDF trovato nella cartella."

    # 2. Estrazione del testo
    testo_unito = ""
    try:
        with fitz.open(file_pdf) as doc:
            for pagina in doc:
                testo_unito += pagina.get_text()
    except Exception as e:
        return f"Errore durante la lettura: {e}"

    testo_finale = " ".join(testo_unito.split())
    return testo_finale

def docx_a_stringa_pulita(percorso_cartella):
    file_docx = None

    # 1. Cerca il primo file .docx nella cartella
    for file in os.listdir(percorso_cartella):
        if file.lower().endswith(".docx") and not file.startswith("~$"):
            file_docx = os.path.join(percorso_cartella, file)
            break

    if not file_docx:
        return "Nessun file .docx trovato."

    # 2. Estrazione del testo
    try:
        doc = docx.Document(file_docx)
        lista_paragrafi = []

        for para in doc.paragraphs:
            if para.text.strip():  # Aggiunge solo se il paragrafo non è vuoto
                lista_paragrafi.append(para.text)

        # Unisce i paragrafi e pulisce ogni residuo di spazi o \n
        testo_unito = " ".join(lista_paragrafi)
        stringa_finale = " ".join(testo_unito.split())

        return stringa_finale

    except Exception as e:
        return f"Errore durante la lettura: {e}"

# async def generate_full_audio(text, filename):
#     # Assicurati che la cartella static esista
#     os.makedirs(os.path.dirname(filename), exist_ok=True)
#
#     # Inizializza la comunicazione con edge_tts
#     #communicate = edge_tts.Communicate(text, "it-IT-GiuseppeNeural")
#     communicate = edge_tts.Communicate(
#         text,
#         voice="it-IT-ElsaNeural",
#         rate="+0%",
#         pitch="+0Hz"
#     )
#
#     # Esegue effettivamente il salvataggio (await è fondamentale)
#     await communicate.save(filename)
#     print(f"File audio generato con successo in: {filename}")

def split_text(text, max_chars=5000):
    """
    Divide il testo in blocchi senza tagliare le parole.
    Cerca di tagliare in corrispondenza di un punto o di un a capo.
    """
    chunks = []
    while len(text) > max_chars:
        # Cerca l'ultimo punto utilizzabile entro il limite max_chars
        split_index = text.rfind('.', 0, max_chars)

        # Se non trova un punto, cerca uno spazio per non tagliare una parola
        if split_index == -1:
            split_index = text.rfind(' ', 0, max_chars)

        # Se non trova nemmeno uno spazio (parola lunghissima), taglia forzatamente
        if split_index == -1:
            split_index = max_chars

        chunks.append(text[:split_index + 1].strip())
        text = text[split_index + 1:]

    chunks.append(text.strip())  # Aggiunge l'ultima parte rimanente
    return chunks


async def convert_large_text(folder_path):
    # # 1. Legge il file di testo
    # if not os.path.exists(file_path):
    #     print("File non trovato!")
    #     return
    #
    # with open(file_path, "r", encoding="utf-8") as f:
    #     full_text = f.read()

    testo = ""
    for file in os.listdir(folder_path):
        if file.lower().endswith(".docx") and not file.startswith("~$"):
            testo = docx_a_stringa_pulita(folder_path)
            break  # Si ferma al primo file trovato
        elif file.lower().endswith(".pdf"):
            testo = estrai_testo_da_cartella(folder_path)
            break  # Si ferma al primo file trovato

    # 2. Suddivide il testo in chunk (blocchi)
    chunks = split_text(testo)
    print(f"Testo totale: {len(testo)} caratteri. Suddiviso in {len(chunks)} blocchi.")

    # 3. Processa ogni blocco
    for i, chunk in enumerate(chunks):
        if not chunk: continue

        output_filename = f"parte_{i + 1:03d}.mp3"
        filepath = os.path.join(folder_path, output_filename)
        # Se il file esiste già, lo saltiamo
        if os.path.exists(filepath):
            print(f"Salto {output_filename}: già esistente.")
            continue

        if not chunk: continue

        print(f"Generazione {output_filename} ({len(chunk)} caratteri)...")

        # Passiamo il testo nativo senza tag SSML per evitare errori di parsing
        communicate = edge_tts.Communicate(chunk, voice="it-IT-ElsaNeural")
        await communicate.save(filepath)

    print("\nConversione completata! Hai ottenuto i file mp3 numerati.")


folder_path = "./static"
if __name__ == "__main__":
    asyncio.run(convert_large_text(folder_path))









