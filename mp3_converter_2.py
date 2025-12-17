import os
import asyncio
import edge_tts
import fitz  # PyMuPDF
import logging
from langchain.docstore.document import Document

folder_path = "./static"
filename = "lettura_completa.mp3"
filepath = os.path.join("./static", filename)
logger = logging.getLogger(__name__)

def extract_text_from_pdfs(folder_path):
    pdf_texts = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(folder_path, filename)
            doc = fitz.open(path)
            logger.info(f"Processing PDF: {filename}")
            text = ""
            for page in doc:
                text += page.get_text()
            pdf_texts.append(text)
    return pdf_texts

def extract_text_from_txts(folder_path):
    txt_texts = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".txt"):
            path = os.path.join(folder_path, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    txt_texts.append(f.read())
                logger.info(f"Processing TXT: {filename}")
            except Exception as e:
                logger.error(f"Errore con {filename}: {e}")
    return txt_texts

async def generate_full_audio(text, filename):
    # Assicurati che la cartella static esista
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Inizializza la comunicazione con edge_tts
    communicate = edge_tts.Communicate(text, "it-IT-GiuseppeNeural")

    # Esegue effettivamente il salvataggio (await è fondamentale)
    await communicate.save(filename)
    print(f"File audio generato con successo in: {filename}")


# --- Testo del racconto su Evaristo ed Eva ---

# Avvio del ciclo asincrono
if __name__ == "__main__":
    pdf_texts = extract_text_from_pdfs(folder_path)
    txt_texts = extract_text_from_txts(folder_path)
    pdf_docs = [Document(page_content=text, metadata={"source": "pdf"}) for text in pdf_texts]
    txt_docs = [Document(page_content=text, metadata={"source": "txt"}) for text in txt_texts]

    if len(pdf_texts) != 0:
        testo = str(pdf_texts)
    elif len(txt_texts) != 0:
        testo = str(txt_texts)
    else:
        testo = ""
        print("Nessun files in folder")

    asyncio.run(generate_full_audio(testo, filepath))