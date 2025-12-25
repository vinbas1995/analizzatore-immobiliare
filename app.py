import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURAZIONE SISTEMA ---
if "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("Configurazione mancante: inserire GEMINI_API_KEY nei Secrets.")
    st.stop()

st.set_page_config(
    page_title="AstaSicura.it | Audit Professionale",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STILE PROFESSIONALE CUSTOM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    .nav-bar {
        background-color: #0f172a;
        padding: 25px;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 20px !important;
        border-radius: 12px;
        border-left: 6px solid #1e3a8a;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .report-card {
        background-color: white;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        font-weight: 600;
        border-radius: 8px;
        width: 100%;
    }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA DI ESTRAZIONE E REPORT ---
def estrai_testo(file_pdf):
    try:
        file_bytes = file_pdf.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        testo = ""
        # Analizziamo le prime 20 pagine per coprire i dati tecnici essenziali
        for pagina in doc[:20]:
            testo += pagina.get_text()
        doc.close()
        return testo if testo.strip() else None
    except Exception:
        return None

def crea_pdf_bytes(dati):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 15, "ASTASICURA.IT - REPORT TECNICO DI AUDIT", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "PUNTEGGI DI RISCHIO (0-10):", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"Urbanistico: {dati['urbano']}", ln=True)
    pdf.cell(190, 8, f"Occupazione: {dati['occupazione']}", ln=True)
    pdf.cell(190, 8, f"Legale: {dati['legale']}", ln=True)
    pdf.cell(190, 8, f"Costi Occulti: {dati['costi']}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "SINTESI PROFESSIONALE:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(190, 7, dati['sintesi'])
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFACCIA WEB ---
st.markdown("""
    <div class="nav-bar">
        <h1 style='margin:0; font-size: 26px;'>ASTASICURA.IT</h1>
        <p style='margin:0; opacity: 0.8; font-size: 14px;'>SISTEMA AUTOMATIZZATO DI ANALISI RISCHI IMMOBILIARI</p>
    </div>
    """, unsafe_allow_html=True)

col_main, col_info = st.columns([2, 1])

with col_main:
    st.markdown("### 📄 Caricamento Perizia")
    file_caricato = st.file_uploader("Trascina qui il file PDF della CTU", type="pdf", label_visibility="collapsed")

with col_info:
    st.markdown("### ℹ️ Nota Metodologica")
    st.caption("Il sistema analizza la conformità urbanistica, lo stato di possesso e la presenza di pesi o vincoli non cancellabili estratti dalla documentazione ufficiale.")

if file_caricato:
    if st.button("ESEGUI ANALISI TECNICA"):
        testo_estratto = estrai_testo(file_caricato)
        
        if not testo_estratto:
            st.error("Impossibile leggere il PDF. Il file potrebbe essere protetto o composto solo da immagini.")
        else:
            try:
                with st.spinner("Calcolo indici di rischio..."):
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = f"""
                    Agisci come esperto legale di AstaSicura.it. Analizza la perizia e restituisci SOLO un JSON:
                    {{
                        "urbano": 0-10, "occupazione": 0-10, "legale": 0-10, "costi": 0-10,
                        "sintesi": "stringa max 150 parole",
                        "verdetto": "stringa breve"
                    }}
                    Testo: {testo_estratto[:28000]}
                    """
                    
                    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    dati = json.loads(response.text)

                    st.markdown("---")
                    st.markdown("## 📊 Risultanze dell'Audit")
                    
                    # Metriche
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Urbanistico", f"{dati['urbano']}/10")
                    m2.metric("Occupazione", f"{dati['occupazione']}/10")
                    m3.metric("Legale", f"{dati['legale']}/10")
                    m4.metric("Oneri", f"{dati['costi']}/10")

                    # Grafico Radar e Sintesi
                    c_chart, c_text = st.columns([1, 1])
                    
                    with c_chart:
                        fig = go.Figure(data=go.Scatterpolar(
                            r=[dati['urbano'], dati['occupazione'], dati['legale'], dati['costi'], dati['urbano']],
                            theta=['Urbanistico', 'Occupazione', 'Legale', 'Costi', 'Urbanistico'],
                            fill='toself', fillcolor='rgba(30, 58, 138, 0.2)', line=dict(color='#1e3a8a', width=3)
                        ))
                        fig.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                            showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)

                    with c_text:
                        st.markdown(f"""
                        <div class="report-card">
                            <h4 style='color:#1e3a8a; margin-top:0;'>📝 Parere Professionale</h4>
                            <p style='font-size: 15px; line-height: 1.6;'>{dati['sintesi']}</p>
                            <div style='background:#f1f5f9; padding:15px; border-radius:8px; border-left:5px solid #1e3a8a;'>
                                <strong>Verdetto finale:</strong> {dati['verdetto']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        pdf_data = crea_pdf_bytes(dati)
                        st.download_button(
                            label="📥 SCARICA REPORT CERTIFICATO PDF",
                            data=pdf_data,
                            file_name=f"Report_AstaSicura_{file_caricato.name}.pdf",
                            mime="application/pdf"
                        )

            except Exception as e:
                st.error(f"Errore durante l'audit. Riprovare con un file diverso.")

st.markdown("<div style='text-align:center; padding:40px; color:#94a3b8; font-size:12px;'>© 2024 AstaSicura.it - Portale Professionale Riservato</div>", unsafe_allow_html=True)
