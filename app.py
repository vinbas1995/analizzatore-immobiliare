import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CHIAVE API ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"

# Configurazione robusta del modello
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usiamo 'gemini-1.5-flash-latest' che è la versione più aggiornata e supportata
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Errore configurazione AI: {e}")

st.set_page_config(page_title="Analizzatore Immobiliare PRO", layout="wide")

def estrai_testo_documento(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_totale = ""
    for pagina in doc:
        testo_pag = pagina.get_text()
        if len(testo_pag) < 100: 
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            testo_pag = pytesseract.image_to_string(img, lang='ita')
        testo_totale += testo_pag
    return testo_totale

# --- INTERFACCIA ---
st.title("⚖️ Valutatore Perizie Immobiliare (Google Gemini AI)")

file_caricato = st.file_uploader("Trascina qui la perizia giudiziaria (PDF)", type="pdf")

if file_caricato:
    if st.button("🚀 AVVIA ANALISI"):
        try:
            with st.spinner("L'IA sta leggendo il documento..."):
                contenuto = estrai_testo_documento(file_caricato)
                
                prompt = f"""
                Agisci come un esperto tecnico-legale immobiliare italiano.
                Analizza questa perizia e produci un report chiaro diviso per punti:
                1. SCORE DI RISCHIO (0-100)
                2. CRITICITÀ RILEVATE (Abusi, pignoramenti, mancanze tecniche)
                3. COSTI ESTIMATIVI DI SANATORIA
                4. CONSIGLIO FINALE (Acquistare o evitare)
                
                Testo della perizia:
                {contenuto[:20000]}
                """
                
                # Chiamata al modello con gestione errori specifica
                response = model.generate_content(prompt)
                
                st.divider()
                st.subheader("📝 Esito dell'Analisi")
                st.markdown(response.text)
                
        except Exception as e:
            # Se dà ancora errore 404, suggerisce di controllare l'account Google Cloud
            st.error(f"Errore durante la generazione: {e}. Assicurati che il modello sia attivo nel tuo Google AI Studio.")
else:
    st.info("👋 Carica un file PDF per iniziare.")

