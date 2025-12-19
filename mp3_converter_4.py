import os
import asyncio
import edge_tts
import docx
import fitz  # PyMuPDF

# === CONFIG ===
os.environ['http_proxy'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['HTTP_PROXY'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['https_proxy'] = "http://proxy.dcl.tetrapak.com:8080"
os.environ['HTTPS_PROXY'] = "http://proxy.dcl.tetrapak.com:8080"

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
async def generate_full_audio(text, filename):
    # Assicurati che la cartella static esista
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Inizializza la comunicazione con edge_tts
    communicate = edge_tts.Communicate(text, "it-IT-GiuseppeNeural")

    # Esegue effettivamente il salvataggio (await è fondamentale)
    await communicate.save(filename)
    print(f"File audio generato con successo in: {filename}")

testo = ""
testo_pdf = ""
testo_doc = ""
folder_path = "./static"
testo_pdf = estrai_testo_da_cartella(folder_path)
if len(testo_pdf) == 0:
    testo_doc = docx_a_stringa_pulita(folder_path)
    if len(testo_doc) == 0:
        print("Nessun files in folder")
    else:
        testo = testo_doc
else:
    testo = testo_pdf

filename = "lettura_completa.mp3"
filepath = os.path.join("./static", filename)

# Avvio del ciclo asincrono
if __name__ == "__main__":
    asyncio.run(generate_full_audio(testo, filepath))