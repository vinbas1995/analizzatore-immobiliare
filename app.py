import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF
import json
import re

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="ASTA-SAFE AI | Portale Analisi Multidocumentale",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SETUP API KEY ---
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# --- STILE CSS AVANZATO (UI WEB PRO) ---
# ==========================================
st.markdown("""
    <style>
    /* Reset e Font globale */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #f4f7f6 !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* --- HEADER WEB --- */
    .web-header {
        background-color: #111827;
        padding: 1rem 2rem;
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 4px solid #3b82f6;
        margin-bottom: 2rem;
        position: fixed; top: 0; left: 0; width: 100%; z-index: 999;
    }
    .logo-area { display: flex; align-items: center; gap: 10px; }
    .logo-text { font-size: 1.5rem; font-weight: 700; letter-spacing: -1px; }
    .logo-sub { color: #9ca3af; font-size: 0.9rem; }
    .main-content { margin-top: 80px; padding-bottom: 100px; }

    /* --- CARD STILIZZATE --- */
    .styled-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    .card-title {
        color: #1f2937;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #f3f4f6;
        padding-bottom: 0.5rem;
    }

    /* --- PULSANTI UI --- */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
        width: 100%;
        transition: all 0.3s;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-2px);
    }

    /* --- GRAFICA BENCHMARK (Progress Bars) --- */
    .metric-row { margin-bottom: 1.2rem; }
    .metric-label-area { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .metric-name { font-weight: 600; color: #4b5563; font-size: 0.9rem; }
    .metric-value { font-weight: 700; font-size: 1rem; }
    
    .bar-bg {
        background-color: #e5e7eb;
        border-radius: 999px;
        height: 14px;
        width: 100%;
        overflow: hidden;
    }
    .bar-fill { height: 100%; border-radius: 999px; }
    
    .critical { background-color: #ef4444; } /* Rosso */
    .warning { background-color: #f97316; }  /* Arancione */
    .good { background-color: #22c55e; }     /* Verde */

    /* --- UPLOAD GRID STILE --- */
    .upload-label { font-weight: bold; color: #374151; margin-bottom: 5px; display: block;}
    
    /* --- FOOTER --- */
    .web-footer {
        background-color: #1f2937;
        color: #9ca3af;
        padding: 3rem 2rem;
        margin-top: 4rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- FUNZIONI ---
# ==========================================

def render_header():
    st.markdown("""
        <div class="web-header">
            <div class="logo-area">
                <span style="font-size: 2rem;">🛡️</span>
                <div>
                    <div class="logo-text">ASTA-SAFE<span style="color:#3b82f6">AI</span></div>
                    <div class="logo-sub">Suite Analisi Multidocumentale</div>
                </div>
            </div>
            <div style="color:white; font-weight:600">Enterprise Edition</div>
        </div>
        <div class="main-content"></div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
        <div class="web-footer">
            ASTA-SAFE AI Technologies | Analisi Documentale Integrata
            <br><small>© 2025. Verify all data on official portals.</small>
        </div>
    """, unsafe_allow_html=True)

def render_ad_space(height="90px", label="Banner"):
    st.markdown(f"""
        <div style="background:#f9fafb; border:2px dashed #d1d5db; height:{height}; display:flex; align-items:center; justify-content:center; border-radius:8px; margin:1rem 0; color:#9ca3af; font-weight:bold;">
            SPAZIO PUBBLICITARIO - {label}
        </div>
    """, unsafe_allow_html=True)

def render_benchmark_bar(name, value):
    try:
        val = float(value)
        percent = min(val * 10, 100)
    except:
        val = 0
        percent = 0
        
    color_class = "good"
    if val <= 4: color_class = "critical"
    elif val <= 7: color_class = "warning"
    
    return f"""
    <div class="metric-row">
        <div class="metric-label-area">
            <span class="metric-name">{name}</span>
            <span class="metric-value {color_class}-text">{val}/10</span>
        </div>
        <div class="bar-bg">
            <div class="bar-fill {color_class}" style="width: {percent}%;"></div>
        </div>
    </div>
    """

def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_da_file(file_obj, nome_tipo):
    """Estrae testo e aggiunge etichetta di origine"""
    if file_obj is None:
        return ""
    
    testo_temp = ""
    try:
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")
        # Analizza max 15 pagine per file per evitare timeout
        pages_to_scan = min(len(doc), 15)
        
        for i, pagina in enumerate(doc):
            if i >= pages_to_scan: break
            t = pagina.get_text()
            # Se poco testo (es. planimetria scansionata), usa OCR
            if len(t) < 50: 
                try:
                    pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    t = pytesseract.image_to_string(img, lang='ita')
                except: t = ""
            testo_temp += t
    except Exception as e:
        return f"[Errore lettura {nome_tipo}: {e}]"

    # Aggiungi separatori chiari per l'IA
    return f"\n\n--- INIZIO DOCUMENTO: {nome_tipo.upper()} ---\n{testo_temp}\n--- FINE DOCUMENTO {nome_tipo.upper()} ---\n"

# ==========================================
# --- APP LOGIC ---
# ==========================================

render_header()
container = st.container()

with container:
    st.markdown("<h1>Dashboard Analisi Integrata</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#6b7280; margin-top:-10px;'>Carica i diversi documenti dell'asta. L'IA incrocerà i dati (es. Perizia vs Catasto) per un benchmark preciso.</p>", unsafe_allow_html=True)
    
    render_ad_space(height="80px", label="Top Leaderboard")

    # --- INPUT ECONOMICI ---
    st.markdown('<div class="styled-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">1. Parametri Economici</div>', unsafe_allow_html=True)
    ce1, ce2 = st.columns(2)
    with ce1: base = st.number_input("Prezzo Base (€)", value=100000, step=1000)
    with ce2: min_bid = st.number_input("Offerta Minima (€)", value=75000, step=1000)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- UPLOAD MULTIPLO (GRIGLIA) ---
    st.markdown('<div class="styled-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">2. Caricamento Documentazione (PDF)</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    # 1 - PERIZIA
    with c1:
        st.markdown('<span class="upload-label">📄 1. Perizia CTU (Principale)</span>', unsafe_allow_html=True)
        file_perizia = st.file_uploader("", type="pdf", key="u1")
        
        st.markdown('<span class="upload-label" style="margin-top:15px">📐 2. Planimetria</span>', unsafe_allow_html=True)
        file_planimetria = st.file_uploader("", type="pdf", key="u2")

    # 2 - ALTRI DOCS
    with c2:
        st.markdown('<span class="upload-label">📢 3. Avviso di Vendita</span>', unsafe_allow_html=True)
        file_avviso = st.file_uploader("", type="pdf", key="u3")
        
        st.markdown('<span class="upload-label" style="margin-top:15px">🏛️ 4. Dati Catastali / Visura</span>', unsafe_allow_html=True)
        file_catasto = st.file_uploader("", type="pdf", key="u4")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Pulsante Azione
    start_analysis = False
    if file_perizia or file_planimetria or file_avviso or file_catasto:
        start_analysis = st.button("🚀 COMBINA DOCUMENTI E AVVIA ANALISI")
    else:
        st.info("Carica almeno un documento (preferibilmente la Perizia) per iniziare.")

    # --- ELABORAZIONE ---
    if start_analysis:
        with st.spinner("🔄 L'IA sta leggendo e incrociando i dati di tutti i file..."):
            
            # 1. Aggregazione Testo
            full_corpus = ""
            files_loaded = []
            
            if file_perizia: 
                full_corpus += estrai_testo_da_file(file_perizia, "PERIZIA CTU")
                files_loaded.append("Perizia")
            if file_planimetria: 
                full_corpus += estrai_testo_da_file(file_planimetria, "PLANIMETRIA")
                files_loaded.append("Planimetria")
            if file_avviso: 
                full_corpus += estrai_testo_da_file(file_avviso, "AVVISO VENDITA")
                files_loaded.append("Avviso")
            if file_catasto: 
                full_corpus += estrai_testo_da_file(file_catasto, "DATI CATASTALI")
                files_loaded.append("Catasto")

            if len(full_corpus) < 100:
                st.error("Errore: Testo insufficiente estratto. I PDF potrebbero essere immagini non leggibili.")
                st.stop()

            # 2. Setup AI
            model = genai.GenerativeModel("models/gemini-1.5-flash")

            # 3. Prompt Multi-Doc
            prompt = f"""
            Agisci come Senior Real Estate Analyst. Hai a disposizione il testo estratto da vari documenti ({', '.join(files_loaded)}).
            
            OBIETTIVO: Analizzare la coerenza tra i documenti e rilevare rischi.
            
            Genera la risposta in DUE PARTI separate da "==SEPARATOR==".

            PARTE 1: JSON PURO (per grafici)
            Restituisci un oggetto JSON con chiavi esatte: "urbanistico", "occupazione", "legale", "economico".
            Valore da 1 (Rischio Estremo) a 10 (Sicuro).
            
            PARTE 2: REPORT MARKDOWN PROFESSIONALE
            Struttura il report così:
            1. **Discrepanze Rilevate**: Se presenti, evidenzia differenze tra Perizia e Catasto/Planimetria (es. stanze abusive, difformità grafiche descritte).
            2. **Analisi Urbanistica**: Stato legittimità e costi sanatoria.
            3. **Stato Occupativo**: Analizza titolo opponibile (da Avviso/Perizia).
            4. **Analisi Economica**: Base d'asta €{base} vs Valore stimato (cerca nel testo). Convenienza?
            5. **Conclusioni**: "Go", "No-Go", o "Caution".

            TESTO COMBINATO DOCUMENTI:
            {full_corpus[:28000]}
            """

            try:
                response = model.generate_content(prompt)
                full_resp = response.text
                
                # Parsing
                if "==SEPARATOR==" in full_resp:
                    json_raw, md_raw = full_resp.split("==SEPARATOR==")
                    json_clean = re.sub(r'```json|```', '', json_raw).strip()
                    try:
                        scores = json.loads(json_clean)
                    except:
                        scores = None
                else:
                    scores = None
                    md_raw = full_resp

                # 4. Output Grafico
                st.markdown("---")
                render_ad_space(height="100px", label="Mid Content")
                
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<h2>📊 Benchmark di Rischio Multidocumentale</h2>', unsafe_allow_html=True)
                
                if scores:
                    c_g1, c_g2 = st.columns(2)
                    with c_g1:
                        st.markdown(render_benchmark_bar("Urbanistica & Conformità", scores.get("urbanistico", 5)), unsafe_allow_html=True)
                        st.markdown(render_benchmark_bar("Stato Occupativo", scores.get("occupazione", 5)), unsafe_allow_html=True)
                    with c_g2:
                        st.markdown(render_benchmark_bar("Vincoli Giuridici", scores.get("legale", 5)), unsafe_allow_html=True)
                        st.markdown(render_benchmark_bar("Convenienza Economica", scores.get("economico", 5)), unsafe_allow_html=True)
                else:
                    st.warning("Grafico non disponibile (Errore parsing JSON). Leggere report testuale.")
                st.markdown('</div>', unsafe_allow_html=True)

                # 5. Output Testuale
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown(f"### 📝 Report Analisi Incrociata ({len(files_loaded)} documenti)", unsafe_allow_html=True)
                st.markdown(md_raw)
                st.markdown('</div>', unsafe_allow_html=True)

                # 6. PDF Export
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Report ASTA-SAFE Multi-Doc", 0, 1, 'C')
                pdf.set_font("Arial", size=10)
                pdf.ln(5)
                pdf.multi_cell(0, 6, clean_text(md_raw.replace("**", "").replace("##", "")))
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                st.download_button("📥 Scarica PDF Completo", pdf_bytes, "Report_Asta_Full.pdf", "application/pdf")

            except Exception as e:
                st.error(f"Errore durante la generazione AI: {e}")

render_footer()
