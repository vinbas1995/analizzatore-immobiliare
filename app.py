import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CONFIGURAZIONE CORE ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# Configurazione Pagina Streamlit
st.set_page_config(page_title="ASTA-SAFE AI Pro", layout="wide", page_icon="⚖️")

# --- FUNZIONI TECNICHE ---

def estrai_testo_ocr(file_pdf):
    """Estrae testo e gestisce PDF scannerizzati tramite OCR."""
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_totale = ""
    for pagina in doc:
        t = pagina.get_text()
        if len(t) < 150: # Se la pagina sembra un'immagine
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            t = pytesseract.image_to_string(img, lang='ita')
        testo_totale += t
    return testo_totale

class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'VALUTAZIONE PROFESSIONALE ASTA GIUDIZIARIA', 0, 1, 'C')
        self.ln(10)

# --- INTERFACCIA UTENTE ---
st.title("🛡️ ASTA-SAFE AI: Analizzatore Pericolosità Immobili")
st.markdown("### Analisi Multidimensionale della Perizia CTU")

with st.sidebar:
    st.header("Parametri Asta")
    prezzo_base = st.number_input("Prezzo Base d'Asta (€)", min_value=0, value=100000, step=5000)
    offerta_min = st.number_input("Offerta Minima (€)", min_value=0, value=75000, step=5000)
    st.divider()
    st.info("L'IA utilizzerà questi dati per calcolare la convenienza economica.")

uploaded_file = st.file_uploader("Carica la Perizia (PDF)", type="pdf")

if uploaded_file:
    if st.button("🚀 GENERA BENCHMARK E ANALISI RISCHI"):
        try:
            with st.spinner("Estrazione dati e consultazione AI in corso..."):
                # 1. Estrazione Testo
                testo_perizia = estrai_testo_ocr(uploaded_file)
                
                # 2. Selezione Modello
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. Prompt
