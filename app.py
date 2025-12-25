import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Perizia AI Pro - Analisi Immobiliare", layout="wide")

# --- FUNZIONI DI SERVIZIO ---
def genera_pdf_report(analisi_testo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"REPORT ANALISI PERIZIA IMMOBILIARE\n\n{analisi_testo}")
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

def estrai_testo_completo(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo = ""
    for pagina in doc:
        testo_pag = pagina.get_text()
        if len(testo_pag) < 100: # Se la pagina è un'immagine/scansione
            pix = pagina.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            testo_pag = pytesseract.image_to_string(img, lang='ita')
        testo += testo_pag
    return testo

# --- INTERFACCIA UTENTE ---
st.title("🛡️ Analizzatore Immobiliare con AI Gemini")
st.markdown("Analisi legale e tecnica automatizzata delle perizie giudiziarie.")

st.sidebar.header("Configurazione AI")
api_key = st.sidebar.text_input("AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88", type="password")

file_caricato = st.file_uploader("Carica la perizia (PDF)", type="pdf")

if file_caricato and api_key:
    if st.button("Avvia Analisi Intelligente"):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            with st.spinner("L'AI sta leggendo e analizzando il documento..."):
                # 1. Estrazione testo (con OCR automatico)
                testo_perizia = estrai_testo_completo(file_caricato)
                
                # 2. Prompt per l'AI
                prompt = f"""
                Agisci come un esperto legale e tecnico immobiliare. 
                Analizza il seguente testo di una perizia e fornisci:
                1. PUNTEGGIO DI PERICOLOSITÀ (0-100).
                2. ELENCO CRITICITÀ: (Urbanistiche, Catastali, Legali, Edilizie).
                3. STIMA COSTI: Una stima dei costi per sanare i problemi trovati.
                4. VERDETTO: L'immobile è mutuabile e sicuro? 
                
                Testo della perizia:
                {testo_perizia[:15000]}
                """
                
                # 3. Chiamata a Gemini
                response = model.generate_content(prompt)
                analisi_ai = response.text

                # 4. Visualizzazione Risultati
                st.divider()
                st.subheader("📝 Resoconto dell'Intelligenza Artificiale")
                st.markdown(analisi_ai)
                
                # 5. Download Report
                pdf_output = genera_pdf_report(analisi_ai)
                st.download_button(
                    label="📥 Scarica Report in PDF",
                    data=pdf_output,
                    file_name="Analisi_AI_Perizia.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Errore durante l'analisi: {e}")
elif not api_key:
    st.info("Inserisci la tua API Key nella barra laterale per attivare l'intelligenza artificiale.")