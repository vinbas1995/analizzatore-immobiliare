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

# --- FUNZIONE PULIZIA TESTO PER PDF ---
def clean_text(text):
    """Rimuove caratteri che mandano in crash la creazione del PDF"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    # Analizziamo max 30 pagine per evitare crash di memoria
    for i, pagina in enumerate(doc):
        if i > 30: break 
        t = pagina.get_text()
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) # Bilanciamento qualità/velocità
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except:
                t = "[Errore OCR su questa pagina]"
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
            with st.spinner("Estrazione testo e analisi AI in corso..."):
                # 1. Selezione Modello Dinamica
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                modello_scelto = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
                model = genai.GenerativeModel(modello_scelto)
                
                # 2. Estrazione
                testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                
                # 3. Prompt Strategico
                prompt = f"""
                Analizza questa perizia per asta giudiziaria italiana. 
                Genera questi BENCHMARK DI PERICOLOSITÀ (voto 1-10):
                - URBANISTICO (Abusi/Sanabilità)
                - OCCUPAZIONE (Stato immobile/Titoli)
                - LEGALE (Vincoli/Servitù)
                - ECONOMICO (Condominio/Sanzioni)
                
                Dati asta: Base €{prezzo_base}, Minima €{offerta_min}.
                Testo: {testo_perizia[:15000]}
                """
                
                response = model.generate_content(prompt)
                analisi_testo = response.text

                # 4. Risultati a Video
                st.divider()
                st.success(f"Analisi completata (Modello: {modello_scelto})")
                st.markdown(analisi_testo)
                
                # 5. Export PDF Pro
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, txt=clean_text(analisi_testo))
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("📥 Scarica Report PDF", data=pdf_bytes, file_name="Analisi_Asta.pdf")

        except Exception as e:
            st.error(f"Errore: {e}")

