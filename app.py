import streamlit as st
import fitz
import pytesseract
from PIL import Image
import io
import google.generativeai as genai

# --- CONFIGURAZIONE ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="ASTA-SAFE AI", layout="wide")

def estrai_testo(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo = ""
    for pagina in doc:
        t = pagina.get_text()
        if len(t) < 100:
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            t = pytesseract.image_to_string(img, lang='ita')
        testo += t
    return testo

# --- INTERFACCIA ---
st.title("⚖️ ASTA-SAFE AI: Valutazione Rischio Giudiziario")
st.sidebar.info("Modello: Gemini 1.5 Real-Time Analysis")

file_caricato = st.file_uploader("Carica Perizia CTU (PDF)", type="pdf")

if file_caricato:
    if st.button("🔍 ANALIZZA BENCHMARK DI RISCHIO"):
        try:
            with st.spinner("L'IA sta calcolando i benchmark di pericolosità..."):
                contenuto = estrai_testo(file_caricato)
                
                # Selezione dinamica modello
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                target_model = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
                model = genai.GenerativeModel(target_model)
                
                prompt = f"""
                Analizza questa perizia per un'asta immobiliare e compila rigorosamente questi benchmark:
                1. RISCHIO URBANISTICO (0-10): Gravità degli abusi (sanabili vs non sanabili).
                2. RISCHIO OCCUPAZIONE (0-10): Stato dell'immobile (libero, occupato dal debitore, occupato con titolo opponibile).
                3. RISCHIO LEGALE (0-10): Presenza di domande giudiziali o vincoli non cancellabili.
                4. COSTI OCCULTI (0-10): Spese condominiali insolute o sanzioni sanatoria elevate.

                Fornisci il risultato in questo formato:
                - PUNTEGGIO TOTALE DI PERICOLOSITÀ
                - TABELLA DEI BENCHMARK
                - ANALISI DETTAGLIATA PER OGNI PUNTO.
                
                Testo: {contenuto[:18000]}
                """
                
                response = model.generate_content(prompt)
                
                # --- VISUALIZZAZIONE RISULTATI ---
                st.divider()
                st.subheader("📊 Dashboard Benchmark di Pericolosità")
                
                # Visualizzazione a Colonne per i Benchmark
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Urbano", "Analisi AI")
                with c2: st.metric("Occupazione", "Analisi AI")
                with c3: st.metric("Legale", "Analisi AI")
                with c4: st.metric("Costi", "Analisi AI")

                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Errore: {e}")
