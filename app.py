import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai

# --- CHIAVE API ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

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

st.title("⚖️ Valutatore Perizie Immobiliare (Multi-Model AI)")

file_caricato = st.file_uploader("Carica la perizia (PDF)", type="pdf")

if file_caricato:
    if st.button("🚀 AVVIA ANALISI"):
        try:
            with st.spinner("Ricerca modello compatibile e analisi in corso..."):
                # 1. Trova il modello disponibile per la tua chiave
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                # Seleziona il primo modello Flash o Pro disponibile
                target_model = "models/gemini-1.5-flash" 
                if target_model not in available_models:
                    target_model = available_models[0] # Prende il primo disponibile se il flash fallisce
                
                model = genai.GenerativeModel(target_model)
                
                # 2. Estrazione testo
                contenuto = estrai_testo_documento(file_caricato)
                
                # 3. Analisi
                prompt = f"""
                Analizza questa perizia immobiliare italiana.
                Sii estremamente preciso su:
                - Abusi edilizi citati.
                - Presenza di ipoteche o pignoramenti.
                - Costi stimati di sanatoria.
                - Se l'immobile è mutuabile.
                
                Testo: {contenuto[:15000]}
                """
                
                response = model.generate_content(prompt)
                
                st.divider()
                st.success(f"Analisi completata con successo usando il modello: {target_model}")
                st.markdown(response.text)
                
        except Exception as e:
            st.error(f"Errore critico: {e}")
            st.info("Consiglio: Controlla su Google AI Studio se hai accettato i termini di servizio del modello.")
