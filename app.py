import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF
import json
import re

# --- 1. CONFIGURAZIONE PAGINA (DEVE ESSERE LA PRIMA RIGA) ---
st.set_page_config(
    page_title="ASTA-SAFE V3.0 Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY (Inserisci la tua qui se quella sotto non va) ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. STILE CSS (QUESTO CAMBIA LA GRAFICA) ---
st.markdown("""
    <style>
    /* Import Font Moderno */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Override Stile Base Streamlit */
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #f3f4f6 !important; /* Grigio chiaro professionale */
    }

    /* Nascondi elementi standard di Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;} 
    .stDeployButton {display:none;}

    /* --- CUSTOM HEADER --- */
    .web-header {
        background-color: #0f172a; /* Blu scurissimo */
        padding: 1.5rem 2rem;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 4px solid #3b82f6; /* Linea blu accesa */
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .logo-text { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.5px; }
    
    /* --- CARD BIANCHE --- */
    .styled-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e5e7eb;
    }
    .card-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f3f4f6;
    }

    /* --- ETICHETTE UPLOAD --- */
    .upload-box-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 5px;
        display: block;
        font-size: 0.9rem;
    }

    /* --- PULSANTE BLU --- */
    .stButton>button {
        background: #2563eb;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.75rem 1rem;
        width: 100%;
        transition: background 0.2s;
    }
    .stButton>button:hover {
        background: #1d4ed8;
    }

    /* --- BARRE GRAFICO --- */
    .metric-row { margin-bottom: 15px; }
    .metric-name { font-size: 0.85rem; font-weight: 600; color: #4b5563; }
    .bar-bg { background-color: #e5e7eb; height: 10px; border-radius: 5px; width: 100%; margin-top: 5px; overflow: hidden;}
    .bar-fill { height: 100%; border-radius: 5px; }
    
    .critical { background-color: #ef4444; }
    .warning { background-color: #f97316; }
    .good { background-color: #10b981; }
    
    /* --- BANNER --- */
    .ad-banner {
        background-color: #f1f5f9;
        border: 2px dashed #cbd5e1;
        color: #64748b;
        text-align: center;
        padding: 10px;
        border-radius: 8px;
        font-size: 0.8rem;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DI UTILITA' ---

def render_header():
    st.markdown("""
        <div class="web-header">
            <div>
                <div class="logo-text">ASTA-SAFE <span style="color:#3b82f6">V3.0</span></div>
                <div style="font-size: 0.9rem; color: #94a3b8;">Enterprise Due Diligence Platform</div>
            </div>
            <div style="text-align:right;">
                <span style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 4px; font-size: 0.8rem;">PRO LICENSE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_banner(label):
    st.markdown(f'<div class="ad-banner">SPAZIO PUBBLICITARIO - {label}</div>', unsafe_allow_html=True)

def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def render_benchmark(label, score):
    try: score = float(score)
    except: score = 0
    
    color = "good"
    if score <= 4: color = "critical"
    elif score <= 7: color = "warning"
    
    percent = min(score * 10, 100)
    
    return f"""
    <div class="metric-row">
        <div style="display:flex; justify-content:space-between;">
            <span class="metric-name">{label}</span>
            <span style="font-weight:bold; font-size:0.9rem;">{score}/10</span>
        </div>
        <div class="bar-bg">
            <div class="bar-fill {color}" style="width: {percent}%;"></div>
        </div>
    </div>
    """

def estrai_pdf(file, tipo):
    if not file: return ""
    text = ""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc: # Legge tutto il file
            t = page.get_text()
            if len(t) < 50: # OCR Fallback minimale
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    t = pytesseract.image_to_string(img, lang='ita')
                except: pass
            text += t
    except: return f"Errore lettura {tipo}"
    return f"\n\n--- DOCUMENTO: {tipo} ---\n{text[:10000]}" # Limito caratteri per sicurezza

# --- 5. LAYOUT PRINCIPALE ---

render_header()

# Banner Top
render_banner("TOP HEADER")

# INPUT PARAMETRI
st.markdown('<div class="styled-card">', unsafe_allow_html=True)
st.markdown('<div class="card-header">1. Parametri Economici</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: base = st.number_input("Prezzo Base Asta (€)", value=100000, step=1000)
with c2: offerta = st.number_input("Offerta Minima (€)", value=75000, step=1000)
st.markdown('</div>', unsafe_allow_html=True)

# INPUT FILES (GRIGLIA 2x2)
st.markdown('<div class="styled-card">', unsafe_allow_html=True)
st.markdown('<div class="card-header">2. Documentazione (Carica i PDF)</div>', unsafe_allow_html=True)

col_up1, col_up2 = st.columns(2)

with col_up1:
    st.markdown('<span class="upload-box-label">📄 Perizia CTU (Obbligatorio)</span>', unsafe_allow_html=True)
    f_perizia = st.file_uploader("", type="pdf", key="p")
    
    st.markdown('<span class="upload-box-label" style="margin-top:15px">📐 Planimetria</span>', unsafe_allow_html=True)
    f_plan = st.file_uploader("", type="pdf", key="pl")

with col_up2:
    st.markdown('<span class="upload-box-label">📢 Avviso di Vendita</span>', unsafe_allow_html=True)
    f_avviso = st.file_uploader("", type="pdf", key="av")
    
    st.markdown('<span class="upload-box-label" style="margin-top:15px">🏛️ Visura Catastale</span>', unsafe_allow_html=True)
    f_catasto = st.file_uploader("", type="pdf", key="ct")

st.markdown('</div>', unsafe_allow_html=True)

# BOTTONE E LOGICA
if f_perizia or f_plan or f_avviso or f_catasto:
    if st.button("🚀 ANALIZZA DOCUMENTI CON IA"):
        with st.spinner("Analisi incrociata in corso... attendere..."):
            
            # Raccolta testo
            testo_totale = ""
            testo_totale += estrai_pdf(f_perizia, "PERIZIA")
            testo_totale += estrai_pdf(f_plan, "PLANIMETRIA")
            testo_totale += estrai_pdf(f_avviso, "AVVISO")
            testo_totale += estrai_pdf(f_catasto, "CATASTO")
            
            # Chiamata AI
            try:
                model = genai.GenerativeModel("models/gemini-1.5-flash")
                prompt = f"""
                Analizza questi documenti di un'asta immobiliare.
                
                OUTPUT RICHIESTO (JSON + MARKDOWN):
                Separati dalla stringa "###SEP###".
                
                PARTE 1: JSON puro. Chiavi: "urb" (urbanistica), "occ" (occupazione), "leg" (legale), "eco" (economico). Voti 1-10.
                
                PARTE 2: Report Markdown.
                - Sintesi dei rischi.
                - Discrepanze tra documenti (es. catasto vs perizia).
                - Calcolo convenienza (Base: {base}€).
                
                TESTO: {testo_totale[:30000]}
                """
                
                resp = model.generate_content(prompt).text
                
                # Parsing
                if "###SEP###" in resp:
                    parti = resp.split("###SEP###")
                    json_str = re.sub(r'```json|```', '', parti[0]).strip()
                    try: 
                        dati = json.loads(json_str)
                    except: 
                        dati = {"urb":5, "occ":5, "leg":5, "eco":5} # Fallback
                    report = parti[1]
                else:
                    dati = {"urb":0, "occ":0, "leg":0, "eco":0}
                    report = resp

                # --- VISUALIZZAZIONE RISULTATI ---
                st.markdown("---")
                render_banner("MID CONTENT")
                
                # GRAFICI
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">📊 Benchmark Rischi</div>', unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown(render_benchmark("Urbanistica", dati.get("urb", 0)), unsafe_allow_html=True)
                    st.markdown(render_benchmark("Occupazione", dati.get("occ", 0)), unsafe_allow_html=True)
                with g2:
                    st.markdown(render_benchmark("Vincoli Legali", dati.get("leg", 0)), unsafe_allow_html=True)
                    st.markdown(render_benchmark("Economia", dati.get("eco", 0)), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # TESTO
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">📝 Report Dettagliato</div>', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, clean_text(report.replace("#", "")))
                st.download_button("Scarica PDF", pdf.output(dest='S').encode('latin-1'), "report.pdf")

            except Exception as e:
                st.error(f"Errore: {e}")

else:
    st.info("Attesa caricamento documenti...")

# Footer
render_banner("FOOTER")
st.markdown("<div style='text-align:center; color:#9ca3af; margin-top:50px;'>ASTA-SAFE V3.0 Enterprise</div>", unsafe_allow_html=True)
