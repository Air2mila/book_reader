import os
import asyncio
import edge_tts


async def generate_full_audio(text, filename):
    # Assicurati che la cartella static esista
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Inizializza la comunicazione con edge_tts
    communicate = edge_tts.Communicate(text, "it-IT-GiuseppeNeural")

    # Esegue effettivamente il salvataggio (await è fondamentale)
    await communicate.save(filename)
    print(f"File audio generato con successo in: {filename}")


# --- Testo del racconto su Evaristo ed Eva ---
testo_pdf = """Evaristo Lancillotti detto Eva e' uno studente universitario ventitreenne nerd del prossimo futuro, siamo nel 2038 per l' appunto. Appassionato di AI si diverte a provare modelli di intelligenza artificiale per le piu' svariate discipline co sup PC nella sua camera/studio. Il mondo e' gia' invaso da piccoli robot umanoidi (quelli con un accenno di testa stilizzato) per lo piu' prodotti dalla ditta cinese Humanoid for Domestic Job (HDJ), questi sono collegati in rete per eventuali SW upgrade e sono equipaggiati di un AI minimale che gli consente di effettuare un certo numero di lavori domestici, spazzare il pavimento, portare oggetti, apparecchiare, accendere la televisione sul canale richiesto, suonare la musica preferita etc. La qualita' di questi robot per contenere i costi non e' eccelsa e son soggetti a frequenti malfunzionamenti e rotture, Eva sviluppa un modello di AI piu' sofisticato che permetta un autodiagnosi e consenta a Tino, cosi' ha soprannominato il suo robottino di casa, una manutenzione preventiva e di ripararsi autonomamente ovviamente previo la disponibilita' dei pezzi di ricambio. Il prompt utilizzato e' "salvaguardare e migliorare la funzionalita' e la tipologia della specie" (intesa come macchina). In ambito domestico tutto procede regolarmente, le parti di ricambio vengono ordinate direttamente online da Tino, Eva le riceve per posta e necessariamente esegue la manutenzione. """

filename = "lettura_completa.mp3"
filepath = os.path.join("./static", filename)

# Avvio del ciclo asincrono
if __name__ == "__main__":
    asyncio.run(generate_full_audio(testo_pdf, filepath))