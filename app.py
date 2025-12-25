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
    page_title="ASTA-SAFE V3.0 Enterprise",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. STILE CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; background-color: #f3f4f6 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} 
    .stDeployButton {display:none;}
    .web-header { background-color: #0f172a; padding: 1.5rem 2rem; color: white; display: flex; align-items: center; justify-content: space-between; border-bottom: 4px solid #3b82f6; margin-bottom: 2rem; }
    .logo-text { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.5px; }
    .styled-card { background-color: white; padding: 2rem; border-radius: 12px; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid #e5e7eb; }
    .card-header { font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 1.5rem; border-bottom: 2px solid #f3f4f6; padding-bottom: 0.5rem; }
    .upload-box-label { font-weight: 600; color: #374151; margin-bottom: 5px; display: block; font-size: 0.9rem; }
    .stButton>button { background: #2563eb; color: white; border-radius: 6px; font-weight: 600; border: none; padding: 0.75rem 1rem; width: 100%; transition: background 0.2s; }
    .stButton>button:hover { background: #1d4ed8; }
    .metric-row { margin-bottom: 15px; }
    .bar-bg { background-color: #e5e7eb; height: 10px; border-radius: 5px; width: 100%; margin-top: 5px; overflow: hidden;}
    .bar-fill { height: 100%; border-radius: 5px; }
    .critical { background-color: #ef4444; } .warning { background-color: #f97316; } .good { background-color: #10b981; }
    .ad-banner { background-color: #f1f5f9; border: 2px dashed #cbd5e1; color: #64748b; text-align: center; padding: 10px; border-radius: 8px; font-size: 0.8rem; margin: 10px 0; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI ---
def render_header():
    st.markdown("""
        <div class="web-header">
            <div><div class="logo-text">ASTA-SAFE <span style="color:#3b82f6">V3.0</span></div>
            <div style="font-size: 0.9rem; color: #94a3b8;">Enterprise Due Diligence Platform</div></div>
            <div><span style="background: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 4px; font-size: 0.8rem;">PRO LICENSE</span></div>
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
    return f"""<div class="metric-row"><div style="display:flex; justify-content:space-between;"><span style="font-weight:600; color:#4b5563;">{label}</span><span style="font-weight:bold;">{score}/10</span></div><div class="bar-bg"><div class="bar-fill {color}" style="width: {percent}%;"></div></div></div>"""

def estrai_pdf(file, tipo):
    if not file: return ""
    text = ""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            t = page.get_text()
            text += t
    except: return f"Errore lettura {tipo}"
    return f"\n\n--- DOCUMENTO: {tipo} ---\n{text[:15000]}"

def trova_modello_disponibile():
    """Cerca un modello valido supportato dalla tua versione API"""
    try:
        modelli = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Priorità di scelta
        preferiti = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        
        for p in preferiti:
            if p in modelli:
                return p
        
        # Se non trova i preferiti, prende il primo disponibile
        if modelli:
            return modelli[0]
        else:
            return None
    except Exception as e:
        return None

# --- 5. APP LOGIC ---

render_header()
render_banner("TOP HEADER")

st.markdown('<div class="styled-card"><div class="card-header">1. Parametri Economici</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1: base = st.number_input("Prezzo Base Asta (€)", value=100000, step=1000)
with c2: offerta = st.number_input("Offerta Minima (€)", value=75000, step=1000)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="styled-card"><div class="card-header">2. Documentazione (Carica i PDF)</div>', unsafe_allow_html=True)
col_up1, col_up2 = st.columns(2)
with col_up1:
    st.markdown('<span class="upload-box-label">📄 Perizia CTU</span>', unsafe_allow_html=True)
    f_perizia = st.file_uploader("", type="pdf", key="p")
    st.markdown('<span class="upload-box-label" style="margin-top:15px">📐 Planimetria</span>', unsafe_allow_html=True)
    f_plan = st.file_uploader("", type="pdf", key="pl")
with col_up2:
    st.markdown('<span class="upload-box-label">📢 Avviso di Vendita</span>', unsafe_allow_html=True)
    f_avviso = st.file_uploader("", type="pdf", key="av")
    st.markdown('<span class="upload-box-label" style="margin-top:15px">🏛️ Visura Catastale</span>', unsafe_allow_html=True)
    f_catasto = st.file_uploader("", type="pdf", key="ct")
st.markdown('</div>', unsafe_allow_html=True)

if f_perizia or f_plan or f_avviso or f_catasto:
    if st.button("🚀 ANALIZZA DOCUMENTI CON IA"):
        with st.spinner("Ricerca modello AI e analisi in corso..."):
            
            # --- SELEZIONE MODELLO DINAMICA ---
            nome_modello = trova_modello_disponibile()
            
            if not nome_modello:
                st.error("ERRORE: La tua API Key non trova nessun modello disponibile. Verifica la chiave o aggiorna la libreria `pip install -U google-generativeai`")
                st.stop()
            
            # st.info(f"Usando il modello: {nome_modello}") # Decommenta per vedere quale usa
            
            testo_totale = ""
            testo_totale += estrai_pdf(f_perizia, "PERIZIA")
            testo_totale += estrai_pdf(f_plan, "PLANIMETRIA")
            testo_totale += estrai_pdf(f_avviso, "AVVISO")
            testo_totale += estrai_pdf(f_catasto, "CATASTO")
            
            try:
                model = genai.GenerativeModel(nome_modello)
                
                prompt = f"""
                Analizza questi documenti di un'asta immobiliare.
                OUTPUT RICHIESTO (JSON + MARKDOWN) separati da "###SEP###".
                
                PARTE 1: JSON puro. Chiavi: "urb" (urbanistica), "occ" (occupazione), "leg" (legale), "eco" (economico). Voti 1-10.
                PARTE 2: Report Markdown. Sintesi rischi, discrepanze e calcolo convenienza (Base: {base}€).
                
                TESTO: {testo_totale[:30000]}
                """
                
                resp = model.generate_content(prompt).text
                
                if "###SEP###" in resp:
                    parti = resp.split("###SEP###")
                    json_str = re.sub(r'```json|```', '', parti[0]).strip()
                    try: dati = json.loads(json_str)
                    except: dati = {"urb":5, "occ":5, "leg":5, "eco":5}
                    report = parti[1]
                else:
                    dati = {"urb":0, "occ":0, "leg":0, "eco":0}
                    report = resp

                st.markdown("---")
                render_banner("MID CONTENT")
                
                st.markdown('<div class="styled-card"><div class="card-header">📊 Benchmark Rischi</div>', unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1:
                    st.markdown(render_benchmark("Urbanistica", dati.get("urb", 0)), unsafe_allow_html=True)
                    st.markdown(render_benchmark("Occupazione", dati.get("occ", 0)), unsafe_allow_html=True)
                with g2:
                    st.markdown(render_benchmark("Vincoli Legali", dati.get("leg", 0)), unsafe_allow_html=True)
                    st.markdown(render_benchmark("Economia", dati.get("eco", 0)), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="styled-card"><div class="card-header">📝 Report Dettagliato</div>', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, clean_text(report.replace("#", "")))
                st.download_button("Scarica PDF", pdf.output(dest='S').encode('latin-1'), "report.pdf")

            except Exception as e:
                st.error(f"Errore durante l'analisi: {e}")

else:
    st.info("Attesa caricamento documenti...")

render_banner("FOOTER")
st.markdown("<div style='text-align:center; color:#9ca3af; margin-top:50px;'>ASTA-SAFE V3.0 Enterprise</div>", unsafe_allow_html=True)
