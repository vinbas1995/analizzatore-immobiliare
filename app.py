import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURAZIONE SICURA ---
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    except Exception as e:
        st.error(f"Errore configurazione API: {e}")
else:
    st.error("Inserisci GEMINI_API_KEY nei Secrets di Streamlit.")
    st.stop()

st.set_page_config(page_title="AstaSicura.it | Audit", layout="wide")

# --- CSS MINIMALE PROFESSIONALE ---
st.markdown("<style>.stMetric {background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #1e3a8a; shadow: 0 2px 4px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)

def estrai_testo(file_pdf):
    try:
        file_bytes = file_pdf.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        testo = ""
        for pagina in doc[:25]: # Analizza fino a 25 pagine
            testo += pagina.get_text()
        doc.close()
        return testo.strip() if len(testo.strip()) > 10 else None
    except Exception as e:
        st.error(f"Errore lettura file: {e}")
        return None

def crea_pdf_bytes(dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "REPORT ASTASICURA.IT", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    # Sostituiamo caratteri non-latin1 per evitare crash del PDF
    sintesi_pulita = dati['sintesi'].encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(190, 10, f"Sintesi: {sintesi_pulita}")
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- UI ---
st.title("⚖️ Portale Analisi AstaSicura.it")
file_caricato = st.file_uploader("Carica CTU (PDF)", type="pdf")

if file_caricato:
    if st.button("ESEGUI AUDIT"):
        testo_perizia = estrai_testo(file_caricato)
        
        if not testo_perizia:
            st.warning("⚠️ Il documento sembra essere una scansione (immagine) o è protetto. L'analisi potrebbe essere meno precisa.")
            testo_perizia = "Analizza questo documento (scansione manuale richiesta)."

        try:
            with st.spinner("Analisi in corso..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                # Prompt con istruzioni di salvataggio
                prompt = f"""
                Analizza questa perizia per AstaSicura.it e restituisci JSON:
                {{ "urbano": 5, "occupazione": 5, "legale": 5, "costi": 5, "sintesi": "testo", "verdetto": "testo" }}
                Usa numeri da 0 a 10.
                Testo: {testo_perizia[:30000]}
                """
                
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                
                # Debug della risposta
                if not response.text:
                    st.error("L'IA non ha restituito dati. Riprova.")
                else:
                    dati = json.loads(response.text)

                    # Visualizzazione
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Urbanistico", f"{dati['urbano']}/10")
                    c2.metric("Occupazione", f"{dati['occupazione']}/10")
                    c3.metric("Legale", f"{dati['legale']}/10")
                    c4.metric("Oneri", f"{dati['costi']}/10")

                    st.info(f"**Verdetto:** {dati['verdetto']}")
                    st.write(dati['sintesi'])
                    
                    # Grafico Radar
                    fig = go.Figure(data=go.Scatterpolar(
                        r=[dati['urbano'], dati['occupazione'], dati['legale'], dati['costi'], dati['urbano']],
                        theta=['Urbano','Occupazione','Legale','Costi','Urbano'],
                        fill='toself', fillcolor='rgba(30, 58, 138, 0.2)', line=dict(color='#1e3a8a')
                    ))
                    st.plotly_chart(fig)

                    # Download
                    pdf_out = crea_pdf_bytes(dati)
                    st.download_button("📥 Scarica Report PDF", pdf_out, "Analisi.pdf", "application/pdf")

        except json.JSONDecodeError:
            st.error("Errore nella formattazione dei dati ricevuti. Riprova.")
        except Exception as e:
            st.error(f"Errore Audit: {str(e)}")
