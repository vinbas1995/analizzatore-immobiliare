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
    page_title="ASTA-SAFE V4.0 Pro Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. API KEY ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. STILE CSS AVANZATO (DASHBOARD STYLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; background-color: #f8fafc !important; }
    
    /* Header */
    .web-header { background: #0f172a; padding: 1.5rem 2rem; color: white; display: flex; justify-content: space-between; align-items: center; border-bottom: 4px solid #3b82f6; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .logo-text { font-size: 1.8rem; font-weight: 800; letter-spacing: -1px; }
    
    /* Card Container */
    .styled-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 25px; border: 1px solid #e2e8f0; }
    .card-header { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin-bottom: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; display: flex; align-items: center; gap: 10px; }
    
    /* GRID SYSTEM PER I BENCHMARK */
    .benchmark-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    
    /* SCORE CARD (La nuova grafica) */
    .score-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .score-card:hover { transform: translateY(-3px); box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
    
    .score-icon { font-size: 2rem; margin-bottom: 5px; display: block; }
    .score-label { font-size: 0.85rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; height: 35px; display: flex; align-items: center; justify-content: center; }
    .score-value { font-size: 2.2rem; font-weight: 800; color: #0f172a; margin: 5px 0; }
    
    /* Progress Bar personalizzata dentro la card */
    .mini-bar-bg { background: #f1f5f9; height: 6px; border-radius: 10px; width: 100%; overflow: hidden; margin-top: 5px; }
    .mini-bar-fill { height: 100%; border-radius: 10px; transition: width 0.5s ease; }
    
    /* Colori Semaforici */
    .bg-red { background-color: #ef4444; }
    .text-red { color: #ef4444 !important; }
    .bg-orange { background-color: #f97316; }
    .text-orange { color: #f97316 !important; }
    .bg-green { background-color: #10b981; }
    .text-green { color: #10b981 !important; }
    
    /* Banner */
    .ad-banner { background: #f8fafc; border: 2px dashed #cbd5e1; color: #94a3b8; padding: 15px; text-align: center; border-radius: 8px; font-weight: 600; font-size: 0.8rem; margin: 20px 0; }
    
    /* Button */
    .stButton>button { background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; border: none; padding: 12px; font-weight: 600; border-radius: 8px; width: 100%; box-shadow: 0 4px 6px rgba(37,99,235,0.2); transition: all 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 8px 12px rgba(37,99,235,0.3); }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DI UTILITÀ ---

def render_header():
    st.markdown("""
        <div class="web-header">
            <div>
                <div class="logo-text">ASTA-SAFE <span style="color:#3b82f6">V4.0</span></div>
                <div style="font-size: 0.9rem; opacity: 0.8;">Real Estate AI Intelligence</div>
            </div>
            <div>
                <span style="background:rgba(255,255,255,0.15); padding:6px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">👑 PREMIUM USER</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_banner(label, height="80px"):
    st.markdown(f'<div class="ad-banner" style="height:{height}; display:flex; align-items:center; justify-content:center;">SPAZIO SPONSOR - {label}</div>', unsafe_allow_html=True)

def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def render_score_card(icon, label, score):
    """Crea una card HTML visivamente accattivante per ogni punteggio"""
    try: score = float(score)
    except: score = 0
    
    # Logica Colori
    if score <= 4: 
        color_class = "bg-red"
        text_class = "text-red"
    elif score <= 7: 
        color_class = "bg-orange"
        text_class = "text-orange"
    else: 
        color_class = "bg-green"
        text_class = "text-green"
        
    percent = min(score * 10, 100)
    
    html = f"""
    <div class="score-card">
        <span class="score-icon">{icon}</span>
        <div class="score-label">{label}</div>
        <div class="score-value {text_class}">{score}<span style="font-size:1rem; color:#94a3b8;">/10</span></div>
        <div class="mini-bar-bg">
            <div class="mini-bar-fill {color_class}" style="width: {percent}%;"></div>
        </div>
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
    return f"\n\n--- DOCUMENTO: {tipo} ---\n{text[:15000]}" # Limitiamo caratteri per efficienza

def trova_modello_disponibile():
    """Trova automaticamente il modello Gemini funzionante"""
    try:
        modelli = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferiti = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        for p in preferiti:
            if p in modelli: return p
        return modelli[0] if modelli else None
    except: return None

# --- 5. LOGICA APPLICAZIONE ---

render_header()
render_banner("TOP LEADERBOARD", "90px")

# INPUT SECTION
st.markdown('<div class="styled-card"><div class="card-header">📊 Parametri e Documenti</div>', unsafe_allow_html=True)
col_param, col_up = st.columns([1, 2])

with col_param:
    st.markdown("**Dati Economici**")
    base = st.number_input("Base d'Asta (€)", value=100000, step=1000)
    offerta = st.number_input("Offerta Minima (€)", value=75000, step=1000)
    st.caption("Questi dati servono per calcolare la convenienza.")

with col_up:
    st.markdown("**Caricamento File (PDF)**")
    c1, c2 = st.columns(2)
    f_perizia = c1.file_uploader("1. Perizia CTU (Fondamentale)", type="pdf")
    f_plan = c2.file_uploader("2. Planimetria", type="pdf")
    f_avviso = c1.file_uploader("3. Avviso Vendita", type="pdf")
    f_catasto = c2.file_uploader("4. Visura Catastale", type="pdf")

st.markdown('</div>', unsafe_allow_html=True)

# ACTION BUTTON
if f_perizia or f_plan or f_avviso or f_catasto:
    if st.button("🚀 AVVIA ANALISI PROFONDA AI"):
        with st.spinner("L'Intelligenza Artificiale sta analizzando la documentazione..."):
            
            # 1. Raccolta Testo
            corpus = ""
            corpus += estrai_pdf(f_perizia, "PERIZIA CTU")
            corpus += estrai_pdf(f_plan, "PLANIMETRIA")
            corpus += estrai_pdf(f_avviso, "AVVISO VENDITA")
            corpus += estrai_pdf(f_catasto, "VISURA CATASTALE")
            
            # 2. Selezione Modello (Auto-fix)
            modello_nome = trova_modello_disponibile()
            if not modello_nome:
                st.error("Errore API: Nessun modello disponibile. Aggiorna libreria.")
                st.stop()
                
            model = genai.GenerativeModel(modello_nome)
            
            # 3. Prompt Esteso (7 Indicatori)
            prompt = f"""
            Analizza questi documenti d'asta immobiliare. Sii estremamente severo e professionale.
            
            OUTPUT RICHIESTO (JSON + MARKDOWN) separati da "###SEP###".
            
            PARTE 1: JSON con 7 chiavi esatte. Voto 1 (Pessimo/Rischio Alto) a 10 (Ottimo/Sicuro).
            Keys:
            - "urb": Conformità Urbanistica (abusi, sanatorie)
            - "occ": Stato Occupativo (libero, occupato con/senza titolo)
            - "leg": Vincoli Legali (pregiudizievoli, servitù)
            - "eco": Convenienza Economica (Prezzo vs Valore mercato)
            - "man": Stato Manutentivo (lavori da fare)
            - "riv": Rivendibilità/Liquidità (facilità di rivendita)
            - "doc": Completezza Documentale (chiarezza perizia)
            
            PARTE 2: Report Markdown Professionale.
            - Analisi dettagliata per ogni punto sopra.
            - Evidenziare "COSTI OCCULTI" se trovati.
            - Conclusione finale: CONSIGLIATO / SCONSIGLIATO.
            
            DATI INPUT: Base: {base}€, Offerta: {offerta}€.
            TESTO DOCUMENTI: {corpus[:32000]}
            """
            
            try:
                resp = model.generate_content(prompt).text
                
                # Parsing
                if "###SEP###" in resp:
                    raw_json, raw_md = resp.split("###SEP###")
                    clean_json = re.sub(r'```json|```', '', raw_json).strip()
                    try: 
                        d = json.loads(clean_json)
                    except: 
                        d = {"urb":5, "occ":5, "leg":5, "eco":5, "man":5, "riv":5, "doc":5}
                    report = raw_md
                else:
                    d = {"urb":0, "occ":0, "leg":0, "eco":0, "man":0, "riv":0, "doc":0}
                    report = resp
                
                # --- VISUALIZZAZIONE NUOVA ---
                st.markdown("---")
                
                # Sezione Benchmark Visivo
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-header">🏆 Scorecard di Rischio (Benchmark AI)</div>', unsafe_allow_html=True)
                
                # Griglia HTML generata dinamicamente
                html_grid = f"""
                <div class="benchmark-grid">
                    {render_score_card("🏗️", "Urbanistica", d.get('urb', 0))}
                    {render_score_card("🏠", "Occupazione", d.get('occ', 0))}
                    {render_score_card("⚖️", "Vincoli Legali", d.get('leg', 0))}
                    {render_score_card("💰", "Economia", d.get('eco', 0))}
                    {render_score_card("🛠️", "Manutenzione", d.get('man', 0))}
                    {render_score_card("📈", "Rivendibilità", d.get('riv', 0))}
                    {render_score_card("📑", "Documenti", d.get('doc', 0))}
                </div>
                """
                st.markdown(html_grid, unsafe_allow_html=True)
                
                # Banner in mezzo
                render_banner("MID REPORT", "100px")
                
                # Report Testuale
                st.markdown('<div class="card-header" style="margin-top:30px;">📝 Analisi Dettagliata</div>', unsafe_allow_html=True)
                st.markdown(report)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # PDF Download
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                # Pulisce caratteri speciali per FPDF
                sanitized_report = clean_text(report.replace("**", "").replace("#", "").replace("###", ""))
                pdf.multi_cell(0, 8, sanitized_report)
                
                st.download_button(
                    label="📥 SCARICA REPORT UFFICIALE (PDF)",
                    data=pdf.output(dest='S').encode('latin-1'),
                    file_name="Analisi_Asta_Full.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Errore analisi: {e}")

render_banner("FOOTER PAGE", "120px")
st.markdown("<div style='text-align:center; padding:30px; color:#cbd5e1;'>ASTA-SAFE V4.0 - Enterprise AI Solutions</div>", unsafe_allow_html=True)
