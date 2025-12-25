import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CONFIGURAZIONE ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="ASTA-SAFE AI Pro", layout="wide")

def clean_text(text):
    """Rimuove caratteri non compatibili con il formato PDF standard"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    for i, pagina in enumerate(doc):
        if i > 30: break 
        t = pagina.get_text()
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except:
                t = "[Errore OCR]"
        testo_risultato += t
    return testo_risultato

# --- INTERFACCIA ---
st.title("🛡️ ASTA-SAFE AI: Valutatore Professionale")

with st.sidebar:
    st.header("Dati Economici")
    prezzo_base = st.number_input("Base d'Asta (€)", value=100000)
    offerta_min = st.number_input("Offerta Minima (€)", value=75000)

uploaded_file = st.file_uploader("Carica Perizia CTU (PDF)", type="pdf")

if uploaded_file:
    if st.button("🚀 GENERA ANALISI BENCHMARK"):
        try:
            with st.spinner("L'IA sta elaborando i dati..."):
                # 1. Modello AI
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 2. Estrazione
                testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                
                # 3. Prompt
                prompt = f"""
                Analizza questa perizia per asta giudiziaria italiana. 
                Genera questi BENCHMARK DI PERICOLOSITÀ (voto 1-10):
                - URBANISTICO (Abusi/Sanabilità)
                - OCCUPAZIONE (Stato immobile/Titoli)
                - LEGALE (Vincoli/Servitù)
                - ECONOMICO (Condominio/Sanzioni)
                
                Testo: {testo_perizia[:15000]}
                """
                
                response = model.generate_content(prompt)
                analisi_testo = response.text

                # 4. Risultati a Video
                st.divider()
                st.subheader("📝 Esito dell'Analisi")
                st.markdown(analisi_testo)
                
                # 5. Export PDF (CORRETTO)
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                # Puliamo il testo prima di inserirlo
                testo_pulito = clean_text(analisi_testo)
                pdf.multi_cell(0, 10, txt=testo_pulito)
                
                # Generiamo i byte del PDF
                pdf_output = pdf.output(dest='S')
                
                # Convertiamo in bytes se necessario (fpdf2 restituisce bytearray o bytes)
                pdf_bytes = bytes(pdf_output)
                
                st.download_button(
                    label="📥 Scarica Report PDF",
                    data=pdf_bytes,
                    file_name="Analisi_Asta.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Errore: {e}")
