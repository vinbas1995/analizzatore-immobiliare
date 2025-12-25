import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CHIAVE API GIÀ INTEGRATA ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# Configurazione Pagina
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
st.success("✅ Intelligenza Artificiale collegata con successo.")

# Caricamento file
file_caricato = st.file_uploader("Trascina qui la perizia giudiziaria (PDF)", type="pdf")

if file_caricato:
    # Mostriamo il tasto solo dopo che il file è stato caricato
    if st.button("🚀 AVVIA ANALISI INTELLIGENTE"):
        try:
            with st.spinner("Analisi in corso... attendi qualche secondo."):
                # 1. Estrazione testo
                contenuto = estrai_testo_documento(file_caricato)
                
                # 2. Modello AI
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. Istruzioni per l'IA
                prompt = f"""
                Analizza questa perizia immobiliare italiana e fornisci:
                - PUNTEGGIO PERICOLOSITÀ (0-100).
                - LISTA CRITICITÀ (Urbanistiche, catastali, ipoteche).
                - STIMA COSTI DI SANATORIA.
                - GIUDIZIO FINALE: L'acquisto è sicuro?
                
                Testo della perizia:
                {contenuto[:15000]}
                """
                
                # 4. Generazione
                risposta = model.generate_content(prompt)
                
                # 5. Risultato a schermo
                st.divider()
                st.subheader("📝 Esito dell'Analisi")
                st.markdown(risposta.text)
                
        except Exception as e:
            st.error(f"Errore tecnico: {e}")
else:
    st.info("👋 Benvenuto! Carica un file PDF per iniziare la valutazione.")
