import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF
import json # Importante per il parsing dei voti
import re

# --- CONFIGURAZIONE PAGINA (Deve essere la prima istruzione) ---
st.set_page_config(
    page_title="ASTA-SAFE AI | Portale Analisi Professionale",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed" # Sidebar chiusa per default per focus su UI web
)

# --- SETUP API KEY ---
# Inserita direttamente come richiesto
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

    /* Nasconde elementi standard Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}

    /* --- HEADER WEB --- */
    .web-header {
        background-color: #111827; /* Dark blue/gray */
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
    .nav-links { display: flex; gap: 20px; font-size: 0.9rem; color: #d1d5db; }

    /* Spaziatura per header fisso */
    .main-content { margin-top: 80px; padding-bottom: 100px; }

    /* --- CARD STILIZZATE --- */
    .styled-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    .card-title {
        color: #1f2937;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 1rem;
        display: flex; align-items: center; gap: 10px;
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
        text-transform: uppercase; letter-spacing: 1px; font-size: 0.85rem;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        transform: translateY(-1px);
    }

    /* --- GRAFICA BENCHMARK (Progress Bars) --- */
    .benchmark-container { margin-top: 1rem; }
    .metric-row { margin-bottom: 1rem; }
    .metric-label-area { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .metric-name { font-weight: 600; color: #4b5563; font-size: 0.9rem; }
    .metric-value { font-weight: 700; font-size: 1rem; }
    
    .bar-bg {
        background-color: #e5e7eb;
        border-radius: 999px;
        height: 12px;
        width: 100%;
        overflow: hidden;
    }
    .bar-fill { height: 100%; border-radius: 999px; transition: width 0.5s ease-in-out; }
    
    /* Colori dinamici classi CSS */
    .critical { background-color: #ef4444; } /* Rosso */
    .warning { background-color: #f97316; }  /* Arancione */
    .good { background-color: #22c55e; }     /* Verde */

    /* --- BANNER AREA --- */
    .ad-placeholder {
        background-color: #f9fafb;
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        color: #6b7280;
        text-align: center;
        padding: 1rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 1rem 0;
    }

    /* --- FOOTER WEB --- */
    .web-footer {
        background-color: #1f2937;
        color: #9ca3af;
        padding: 3rem 2rem;
        margin-top: 4rem;
        text-align: center;
        border-top: 1px solid #374151;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# --- COMPONENTI HTML (COMPONENTI UI) ---
# ==========================================

def render_header():
    st.markdown("""
        <div class="web-header">
            <div class="logo-area">
                <span style="font-size: 2rem;">🛡️</span>
                <div>
                    <div class="logo-text">ASTA-SAFE<span style="color:#3b82f6">AI</span></div>
                    <div class="logo-sub">Professional Due Diligence</div>
                </div>
            </div>
            <div class="nav-links">
                <span>Analisi</span>
                <span>Report</span>
                <span>Prezzi</span>
                <span style="color:white; font-weight:600">Account Pro</span>
            </div>
        </div>
        <div class="main-content"></div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("""
        <div class="web-footer">
            <div style="font-weight:700; color:white; margin-bottom:1rem;">ASTA-SAFE AI Technologies</div>
            <div style="font-size:0.85rem; margin-bottom:2rem;">
                Strumenti avanzati di Intelligenza Artificiale per il Real Estate Giudiziario.<br>
                Via Roma 1, Milano | info@astasafe.ai
            </div>
            <div style="font-size:0.75rem; color:#6b7280;">
                © 2024 Tutti i diritti riservati. L'analisi AI non sostituisce il parere legale/tecnico di un professionista abilitato.
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_ad_space(height="90px", label="Banner"):
    st.markdown(f"""
        <div class="ad-placeholder" style="height: {height}; display:flex; align-items:center; justify-content:center;">
            AREA PUBBLICITARIA - {label}<br>
            (Inserisci codice AdSense qui)
        </div>
    """, unsafe_allow_html=True)

def render_benchmark_bar(name, value):
    """Genera l'HTML per una barra di benchmark stilizzata"""
    try:
        val = float(value)
        percent = val * 10 # Converti scala 1-10 in percentuale
    except:
        val = 0
        percent = 0
        
    # Determina il colore
    color_class = "good"
    if val <= 4: color_class = "critical"
    elif val <= 7: color_class = "warning"
    
    html = f"""
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
    return html

# ==========================================
# --- FUNZIONI LOGICHE (BACKEND) ---
# ==========================================

def clean_text(text):
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    # Analizziamo max 20 pagine per velocizzare UI pro
    progress_bar = st.progress(0, text="Lettura PDF...")
    total = min(len(doc), 20)
    for i, pagina in enumerate(doc):
        if i >= 20: break 
        progress_bar.progress((i + 1) / total, text=f"Elaborazione pagina {i+1}/{total}...")
        t = pagina.get_text()
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.3, 1.3))
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except: t = ""
        testo_risultato += t
    progress_bar.empty()
    return testo_risultato

# ==========================================
# --- CORPO DELLA PAGINA (UI MAIN) ---
# ==========================================

# 1. Render Header Professionale
render_header()

# Layout principale a colonne (Contenuto al centro, banner ai lati se desiderato, qui usiamo full width)
container = st.container()

with container:
    # --- AREA HEADER TITOLO ---
    cols_tit = st.columns([3, 1])
    with cols_tit[0]:
        st.markdown("<h1>Dashboard Analisi Perizie</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#6b7280; margin-top:-15px;'>Carica il documento CTU per ottenere istantaneamente il rating di rischio e l'analisi semantica dell'IA.</p>", unsafe_allow_html=True)
    with cols_tit[1]:
         render_ad_space(height="70px", label="Sponsor Top")

    st.markdown("---")

    # --- LAYOUT INPUT (2 Colonne) ---
    col_in1, col_in2 = st.columns([1, 2])

    with col_in1:
        st.markdown('<div class="styled-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">💰 Dati Asta</div>', unsafe_allow_html=True)
        prezzo_base = st.number_input("Prezzo Base (€)", value=100000, step=5000)
        offerta_min = st.number_input("Offerta Minima (€)", value=75000, step=5000)
        st.markdown('</div>', unsafe_allow_html=True)
        
        render_ad_space(height="200px", label="Banner Laterale")

    with col_in2:
        st.markdown('<div class="styled-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">📂 Caricamento Documento</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Trascina qui la Perizia CTU (PDF)", type="pdf")
        
        st.write("")
        if uploaded_file:
            st.info(f"📄 Documento caricato: {uploaded_file.name}")
            analyze_btn = st.button("🚀 AVVIA ELABORAZIONE IA PRO")
        else:
            analyze_btn = False
        st.markdown('</div>', unsafe_allow_html=True)

    # --- AREA RISULTATI ---
    if uploaded_file and analyze_btn:
        try:
            with st.spinner("🧠 L'Intelligenza Artificiale sta analizzando il documento..."):
                
                # 1. Estrazione
                uploaded_file.seek(0)
                testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                
                if not testo_perizia or len(testo_perizia) < 100:
                    st.error("Impossibile estrarre testo sufficiente dal PDF. Verifica che non sia protetto o danneggiato.")
                    st.stop()

                # 2. Configurazione Modello
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                modello_scelto = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
                model = genai.GenerativeModel(modello_scelto)
                
                # 3. PROMPT AVANZATO (Output strutturato per grafici)
                # Chiediamo specificamente un blocco JSON separato dall'analisi testuale
                prompt = f"""
                Analizza questa perizia giudiziaria italiana.
                Genera DUE blocchi distinti nella risposta, separati da "==SEPARATOR==".

                BLOCCO 1 (SOLO JSON):
                Un oggetto JSON con i voti da 1 a 10 (1 critico, 10 sicuro) per queste categorie. Usa esattamente queste chiavi:
                "urbanistico", "occupazione", "legale", "economico".

                BLOCCO 2 (MARKDOWN):
                Un'analisi professionale dettagliata che giustifica i voti, evidenziando abusi, stati di occupazione, vincoli e costi occulti.

                Dati asta: Base €{prezzo_base}, Minima €{offerta_min}.
                Testo (estratto): {testo_perizia[:20000]}
                """
                
                response = model.generate_content(prompt)
                full_response = response.text

                # 4. Parsing della Risposta
                try:
                    json_part, md_part = full_response.split("==SEPARATOR==")
                    # Pulisce eventuali markdown code blocks attorno al json
                    json_clean = re.sub(r'```json\s*|```', '', json_part.strip())
                    voti_data = json.loads(json_clean)
                except Exception as parse_err:
                    st.warning("Errore nel parsing dei voti visivi. Mostro solo l'analisi testuale.")
                    voti_data = None
                    md_part = full_response # Fallback

                st.markdown("---")
                st.markdown("<h2>📊 Report Finale di Due Diligence</h2>", unsafe_allow_html=True)
                
                render_ad_space(height="90px", label="Sponsor Mid-Content")

                # --- Visualizzazione Grafica (Card dedicata) ---
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">📈 Benchmark Rischio (Voto 1-10)</div>', unsafe_allow_html=True)
                st.markdown('<p style="color:#6b7280; font-size:0.85rem;">Nota: Punteggi bassi indicano alto rischio/criticità.</p>', unsafe_allow_html=True)
                
                if voti_data:
                    col_g1, col_g2 = st.columns(2)
                    with col_g1:
                        st.markdown(render_benchmark_bar("Rischio Urbanistico (Abusi)", voti_data.get("urbanistico", 0)), unsafe_allow_html=True)
                        st.markdown(render_benchmark_bar("Stato Occupativo", voti_data.get("occupazione", 0)), unsafe_allow_html=True)
                    with col_g2:
                        st.markdown(render_benchmark_bar("Vincoli Legali / Servitù", voti_data.get("legale", 0)), unsafe_allow_html=True)
                        st.markdown(render_benchmark_bar("Oneri Economici Condominiali", voti_data.get("economico", 0)), unsafe_allow_html=True)
                else:
                    st.error("Impossibile generare il grafico visivo dei benchmark.")
                
                st.markdown('</div>', unsafe_allow_html=True)

                # --- Visualizzazione Testuale (Card dedicata) ---
                st.markdown('<div class="styled-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">📝 Analisi Dettagliata IA</div>', unsafe_allow_html=True)
                st.markdown(md_part)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- EXPORT PDF ---
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, clean_text("Report ASTA-SAFE AI Pro"), 0, 1, 'C')
                pdf.ln(10)
                pdf.set_font("Arial", size=11)
                # Pulizia base markdown per PDF
                text_for_pdf = clean_text(md_part.replace("**", "").replace("#", ""))
                pdf.multi_cell(0, 7, txt=text_for_pdf)
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                st.download_button("📥 Scarica Report PDF Legale", data=pdf_bytes, file_name=f"Analisi_Asta_{uploaded_file.name}.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"Errore critico durante l'analisi: {e}")

# 3. Render Footer Professionale
render_footer()
