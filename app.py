import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CONFIGURAZIONE API GEMINI ---
# ATTENZIONE: Chiave inserita direttamente come richiesto
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Analizzatore Perizie Immobiliare PRO", layout="wide")

class ReportPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'REPORT TECNICO ANALISI PERIZIA - AI GENERATIVE', 0, 1, 'C')
        self.ln(5)

def estrai_testo_documento(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_totale = ""
    for pagina in doc:
        testo_pag = pagina.get_text()
        if len(testo_pag) < 100: # Se la pagina è una scansione/immagine
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            testo_pag = pytesseract.image_to_string(img, lang='ita')
        testo_totale += testo_pag
    return testo_totale

# --- INTERFACCIA ---
st.title("⚖️ Valutatore Perizie Immobiliare (Google Gemini AI)")
st.info("Sistema configurato con Chiave API dedicata. Pronto all'analisi.")

file_caricato = st.file_uploader("Carica la perizia giudiziaria (PDF)", type="pdf")

if file_caricato:
    if st.button("Analizza con Intelligenza Artificiale"):
        try:
            with st.spinner("L'IA sta studiando il documento (estrazione testo + analisi)..."):
                # 1. Estrazione testo
                contenuto = estrai_testo_documento(file_caricato)
                
                # 2. Configurazione Modello
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. Prompt Specializzato
                prompt = f"""
                Analizza questa perizia immobiliare e fornisci un report professionale:
                - PUNTEGGIO PERICOLOSITÀ (0-100).
                - ANALISI CRITICITÀ (Urbanistiche, catastali, legali).
                - STIMA COSTI DI SANATORIA O RIPRISTINO.
                - CONCLUSIONE: L'immobile è un buon investimento o presenta troppi rischi?
                
                Testo della perizia:
                {contenuto[:15000]}
                """
                
                # 4. Generazione Analisi
                risposta = model.generate_content(prompt)
                risultato_ai = risposta.text

                # 5. Visualizzazione
                st.subheader("📊 Risultato dell'Analisi")
                st.markdown(risultato_ai)
                
                # 6. Generazione PDF per Download
                pdf = ReportPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=11)
                pdf.multi_cell(0, 10, txt=risultato_ai.encode('latin-1', 'ignore').decode('latin-1'))
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                st.download_button(
                    label="📥 Scarica Report PDF",
                    data=pdf_output,
                    file_name="Analisi_Perizia_AI.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Si è verificato un errore: {e}")
