import fitz  # PyMuPDF


def pdf_a_stringa(percorso_pdf):
    testo_totale = ""

    # Apre il documento
    with fitz.open(percorso_pdf) as doc:
        # Cicla attraverso ogni pagina
        for pagina in doc:
            # Estrae il testo della pagina e lo aggiunge alla stringa
            testo_totale += pagina.get_text() + "\n"

    return testo_totale


# Esempio di utilizzo
percorso = ".\static\summary.pdf"
risultato = pdf_a_stringa(percorso)

print(risultato)