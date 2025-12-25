import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF
import json
import re

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="ASTA-SAFE V4.1 Pro Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY ---
# INSERISCI QUI LA TUA CHIAVE
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. STILE CSS AVANZATO (NEON RADIAL GAUGE DASHBOARD) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Rajdhani:wght@700&display=swap');
    
    html, body, [class*="css"]  { 
        font-family: 'Inter', sans-serif; 
        background-color: #080f1a !important; 
        color: #f1f5f9;
    }
    
    .web-header { 
        background: transparent; 
        padding: 1.5rem 2rem; 
        color: white; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-bottom: 2px solid #162a45; 
        margin-bottom: 2rem; 
    }
    .logo-text { 
        font-family: 'Rajdhani', sans-serif;
        font-size: 2rem; 
        font-weight: 800; 
        letter-spacing: -1px; 
        color: #f1f5f9;
    }
    
    .styled-card { 
        background: rgba(17, 24, 39, 0.8); 
        padding: 25px; 
        border-radius: 15px; 
        border: 1px solid #1f2937; 
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(4px); 
        margin-bottom: 25px;
    }
    .card-header { 
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.5rem; 
        font-weight: 700; 
        color: #f1f5f9; 
        margin-bottom: 20px; 
        border-bottom: 2px solid #1f2937; 
        padding-bottom: 10px; 
        display: flex; 
        align-items: center; 
        gap: 10px; 
    }
    
    .benchmark-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 25px;
        margin-bottom: 20px;
    }
    
    .gauge-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        position: relative;
        transition: transform 0.2s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .gauge-card:hover { 
        transform: translateY(-5px); 
        box-shadow: 0 10px 30px rgba(34, 197, 94, 0.2); 
    }
    
    .gauge-icon { font-size: 2rem; color: #6b7280; margin-bottom: 10px; display: block; }
    
    .gauge-score {
        position: absolute; top: 50%; left: 50%;
        transform: translate(-50%, -30%); text-align: center;
    }
    .gauge-score-value {
        font-family: 'Rajdhani', sans-serif; font-size: 2.8rem; font-weight: 800; color: #f1f5f9; line-height: 1;
    }
    .gauge-score-max { font-size: 1rem; color: #6b7280; font-weight: 400; }
    
    .gauge-label { 
        font-size: 0.95rem; color: #f1f5f9; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px;
    }
    
    .gauge-ring-container { position: relative; width: 180px; height: 180px; margin: 0 auto; }
    .gauge-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
    .gauge-circle-bg { fill: none; stroke: #1f2937; stroke-width: 12px; }
    .gauge-circle-prog { fill: none; stroke-width: 12px; stroke-linecap: round; transition: stroke-dashoffset 1s ease, stroke 0.3s ease; }
    
    .neon-red { stroke: #ef4444; filter: drop-shadow(0 0 6px #ef4444); }
    .neon-orange { stroke: #f97316; filter: drop-shadow(0 0 6px #f97316); }
    .neon-green { stroke: #22c55e; filter: drop-shadow(0 0 6px #22c55e); }
    
    .ad-banner { background: #111827; border: 2px dashed #374151; color: #6b7280; padding: 15px; text-align: center; border-radius: 8px; font-weight: 600; font-size: 0.8rem; margin: 20px 0; }
    
    .stButton>button { background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); color: white; border: none; padding: 12px; font-weight: 600; border-radius: 8px; width: 100%; box-shadow: 0 4px 10px rgba(34,197,94,0.3); transition: all 0.3s; text-transform: uppercase; letter-spacing: 1px; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 8px 20px rgba(34,197,94,0.4); }
    
    .stNumberInput, .stFileUploader { border-radius: 8px; background: #111827; border: 1px solid #1f2937; color: #f1f5f9; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DI UTILITÀ ---

def render_header():
    st.markdown("""
        <div class="web-header">
            <div>
                <div class="logo-text">ASTA-SAFE <span style="color:#22c55e">V4.1</span> Pro Dashboard</div>
                <div style="font-size: 0.9rem; opacity: 0.8; color: #94a3b8;">Real Estate AI Intelligence • Enterprise Edition</div>
            </div>
            <div>
                <span style="background:rgba(34,197,94,0.15); color: #22c55e; padding:8px 16px; border-radius:20px; font-size:0.85rem; font-weight:600; border: 1px solid rgba(34,197,94,0.3);">👑 PREMIUM LICENSE</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_banner(label, height="80px"):
    st.markdown(f'<div class="ad-banner" style="height:{height}; display:flex; align-items:center; justify-content:center;">SPAZIO SPONSOR • {label}</div>', unsafe_allow_html=True)

def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def render_radial_gauge(icon, label, score):
    try: score = float(score)
    except: score = 0
    
    if score <= 4: color_neon = "neon-red"
    elif score <= 7: color_neon = "neon-orange"
    else: color_neon = "neon-green"
        
    max_score = 10
    circle_circumference = 502.65
    score_scaled = min(max(score, 0), 10)
    progress_offset = circle_circumference - (score_scaled / max_score) * circle_circumference
    
    html = f"""
    <div class="gauge-card">
        <div class="gauge-ring-container">
            <svg class="gauge-svg" viewBox="0 0 180 180">
                <circle class="gauge-circle-bg" cx="90" cy="90" r="80" />
                <circle class="gauge-circle-prog {color_neon}" cx="90" cy="90" r="80" stroke-dasharray="{circle_circumference}" stroke-dashoffset="{progress_offset}" />
            </svg>
            <div class="gauge-score">
                <span class="gauge-score-value">{score_scaled}</span><span class="gauge-score-max">/{max_score}</span>
            </div>
        </div>
        <span class="gauge-icon">{icon}</span>
        <div class="gauge-label">{label}</div>
    </div>
    """
    return html

def estrai_pdf(file, tipo):
    if not file: return ""
    text = ""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            t = page.get_text()
            text += t
    except: return f" Errore {tipo} "
    return f"\n\n--- DOCUMENTO: {tipo} ---\n{text[:15000]}"

def trova_modello_sicuro():
    """Tenta di forzare un modello funzionante anche con librerie vecchie"""
    try:
        # Tenta prima di vedere se i modelli moderni sono nella lista
        models = [m.name for m in genai.list_models()]
        if 'models/gemini-1.5-flash' in models:
            return 'models/gemini-1.5-flash'
        elif 'models/gemini-pro' in models:
            return 'models/gemini-pro'
        
        # Se la lista è vuota o strana (bug libreria vecchia), FORZA gemini-pro
        return 'gemini-pro'
    except:
        # Se crasha proprio list_models(), FORZA gemini-pro
        return 'gemini-pro'

# --- 5. LOGICA APPLICAZIONE ---

render_header()
render_banner("TOP LEADERBOARD DASHBOARD", "90px")

st.markdown('<div class="styled-card"><div class="card-header">📊 Parametri e Documentazione d\'Ingresso</div>', unsafe_allow_html=True)
col_param, col_up = st.columns([1, 2])

with col_param:
    st.markdown("**Dati Economici Asta**")
    base = st.number_input("Base d'Asta (€)", value=100000, step=1000, key="asta_base")
    offerta = st.number_input("Offerta Minima (€)", value=75000, step=1000, key="asta_offerta")
    st.caption("Questi dati servono per calcolare la convenienza d'investimento.")

with col_up:
    st.markdown("**Caricamento Documenti (Formato PDF)**")
    c1, c2 = st.columns(2)
    f_perizia = c1.file_uploader("1. Perizia CTU (Principale)", type="pdf", key="up_perizia")
    f_plan = c2.file_uploader("2. Planimetria", type="pdf", key="up_planimetria")
    f_avviso = c1.file_uploader("3. Avviso Vendita", type="pdf", key="up_avviso")
    f_catasto = c2.file_uploader("4. Visura Catastale / Dati", type="pdf", key="up_catasto")

st.markdown('</div>', unsafe_allow_html=True)

if f_perizia or f_plan or f_avviso or f_catasto:
    if st.button("🚀 AVVIA ANALISI PROFONDA AI V4.1"):
        with st.spinner("🕵️ Analisi documenti in corso..."):
            
            corpus = ""
            corpus += estrai_pdf(f_perizia, "PERIZIA CTU")
            corpus += estrai_pdf(f_plan, "PLANIMETRIA")
            corpus += estrai_pdf(f_avviso, "AVVISO VENDITA")
            corpus += estrai_pdf(f_catasto, "VISURA CATASTALE")
            
            # Utilizzo funzione "Blind Fix"
            modello_nome = trova_modello_sicuro()
            model = genai.GenerativeModel(modello_nome)
            
            prompt = f"""
            Agisci come Senior Real Estate Analyst. Analizza questi documenti d'asta.
            OUTPUT RICHIESTO: JSON separato da "###SEP###" e Report Markdown.
            
            JSON KEYS (voto 1-10): "urb", "occ", "leg", "eco", "man", "riv", "doc".
            
            DATI INPUT ASTA: Base €{base}, Offerta €{offerta}.
            TESTO DOCUMENTI: {corpus[:30000]}
            """
            
            try:
                resp = model.generate_content(prompt).text
                
                if "###SEP###" in resp:
                    raw_json, raw_md = resp.split("###SEP###")
                    clean_json = re.sub(r'```json|```', '', raw_json).strip()
                    try: d = json.loads(clean_json)
                    except: d = {"urb":5, "occ":5, "leg":5, "eco":5, "man":5, "riv":5, "doc":5}
                    report = raw_md
                else:
                    d = {"urb":0, "occ":0, "leg":0, "eco":0, "man":0, "riv":0, "doc":0}
                    report = resp
                
                st.markdown("---")
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">🏆 Dashboard Scorecard</div>', unsafe_allow_html=True)
                
                html_grid = f"""
                <div class="benchmark-grid">
                    {render_radial_gauge("🏗️", "Urbanistica", d.get('urb', 0))}
                    {render_radial_gauge("🏠", "Occupazione", d.get('occ', 0))}
                    {render_radial_gauge("⚖️", "Vincoli Legali", d.get('leg', 0))}
                    {render_radial_gauge("💰", "Economia", d.get('eco', 0))}
                    {render_radial_gauge("🛠️", "Manutenzione", d.get('man', 0))}
                    {render_radial_gauge("📈", "Rivendibilità", d.get('riv', 0))}
                    {render_radial_gauge("📑", "Documenti", d.get('doc', 0))}
                </div>
                """
                st.markdown(html_grid, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                render_banner("MID REPORT DASHBOARD", "100px")
                
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">📝 Analisi Dettagliata</div>', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                sanitized_report = clean_text(report.replace("**", "").replace("#", ""))
                pdf.multi_cell(0, 8, sanitized_report)
                
                st.download_button("📥 SCARICA REPORT PDF", pdf.output(dest='S').encode('latin-1'), "Analisi_Full.pdf")
                
            except Exception as e:
                st.error(f"Errore: {e}. PROVA AD AGGIORNARE LA LIBRERIA: pip install -U google-generativeai")

else:
    st.info("Attesa caricamento documentazione...")

render_banner("FOOTER DASHBOARD PAGE", "120px")
st.markdown("<div style='text-align:center; padding:30px; color:#6b7280;'>ASTA-SAFE AI Dashboard V4.1 Pro</div>", unsafe_allow_html=True)
