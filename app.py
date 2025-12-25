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

st.set_page_config(page_title="ASTA-SAFE AI Pro", layout="wide", page_icon="⚖️")

# --- FUNZIONI TECNICHE ---

def estrai_testo_ocr(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    for pagina in doc:
        t = pagina.get_text()
        if len(t) < 150: 
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            t = pytesseract.image_to_string(img, lang='ita')
        testo_risultato += t
    return testo_risultato

class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'REPORT VALUTAZIONE ASTA GIUDIZIARIA', 0, 1, 'C')
        self.ln(10)

# --- INTERFACCIA UTENTE ---
st.title("🛡️ ASTA-SAFE AI: Analizzatore Pericolosità")

with st.sidebar:
    st.header("Parametri Economici")
    prezzo_base = st.number_input("Prezzo Base d'Asta (€)", min_value=0, value=100000)
    offerta_min = st.number_input("Offerta Minima (€)", min_value=0, value=75000)

uploaded_file = st.file_uploader("Carica la Perizia (PDF)", type="pdf")

if uploaded_file:
    if st.button("🚀 AVVIA ANALISI BENCHMARK"):
        try:
            with st.spinner("Ricerca modello AI compatibile e analisi..."):
                # 1. Trova il miglior modello disponibile per la tua chiave (Risolve errore 404)
                modelli_disponibili = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                # Cerchiamo in ordine di preferenza
                preferiti = ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "models/gemini-pro"]
                modello_scelto = next((m for m in preferiti if m in modelli_disponibili), modelli_disponibili[0])
                
                model = genai.GenerativeModel(modello_scelto)
                
                # 2. Estrazione Testo
                testo_perizia = estrai_testo_ocr(uploaded_file)
                
                # 3. Prompt Benchmark
                prompt = f"""
                Analizza questa perizia per asta giudiziaria e genera i seguenti BENCHMARK DI PERICOLOSITÀ (voto 1-10):
                - RISCHIO URBANISTICO: Gravità abusi e costi ripristino.
                - RISCHIO OCCUPAZIONE: Stato immobile e tempi di liberazione.
                - RISCHIO LEGALE: Vincoli non cancellabili e servitù.
                - RISCHIO ECONOMICO: Oneri condominiali e sanzioni.
                
                Dati asta: Base €{prezzo_base}, Minima €{offerta_min}.
                Testo: {testo_perizia[:15000]}
                """
                
                response = model.generate_content(prompt)
                analisi_testo = response.text

                # 4. Risultati
                st.divider()
                st.success(f"Analisi completata con successo (Modello utilizzato: {modello_scelto})")
                st.markdown(analisi_testo)
                
                # 5. Export PDF
                pdf = ReportPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=11)
                pdf.multi_cell(0, 10, txt=analisi_testo.encode('latin-1', 'ignore').decode('latin-1'))
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="📥 Scarica Report PDF", data=pdf_bytes, file_name="Analisi_Asta.pdf")

        except Exception as e:
            st.error(f"Errore durante l'analisi: {e}")
            st.info("Nota: Assicurati che la chiave API sia attiva in Google AI Studio.")
