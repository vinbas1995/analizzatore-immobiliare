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

# --- AGGIUNGI QUI IL CSS PER LA BELLA INTERFACCIA ---
st.markdown("""
<style>
    :root {
        --primary: #2563eb;
        --primary-dark: #1d4ed8;
        --secondary: #0f172a;
        --accent: #f59e0b;
        --light: #f8fafc;
        --gray: #64748b;
        --gray-light: #e2e8f0;
        --danger: #ef4444;
        --success: #10b981;
        --border-radius: 12px;
        --shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    }
    
    .main {
        background-color: #f1f5f9;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .logo-icon {
        background-color: #2563eb;
        color: white;
        width: 44px;
        height: 44px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 22px;
    }
    
    .logo-text h1 {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }
    
    .logo-text p {
        font-size: 13px;
        color: #64748b;
        font-weight: 500;
        margin: 0;
    }
    
    .sidebar-section h2 {
        font-size: 18px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
    }
    
    .value-display {
        background-color: #f0f9ff;
        border-radius: 12px;
        padding: 15px;
        margin-top: 10px;
        border-left: 4px solid #2563eb;
    }
    
    .value-display p {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 5px;
    }
    
    .value-display h3 {
        font-size: 22px;
        font-weight: 700;
        color: #2563eb;
        margin: 0;
    }
    
    .upload-section {
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 30px;
        text-align: center;
        border: 3px dashed #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: #2563eb;
    }
    
    .upload-icon {
        font-size: 48px;
        color: #2563eb;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        font-size: 24px;
    }
    
    .stat-icon.urban {
        background-color: #dbeafe;
        color: #1d4ed8;
    }
    
    .stat-icon.occupation {
        background-color: #fef3c7;
        color: #d97706;
    }
    
    .stat-icon.legal {
        background-color: #fce7f3;
        color: #be185d;
    }
    
    .stat-icon.economic {
        background-color: #dcfce7;
        color: #15803d;
    }
    
    .stat-info h3 {
        font-size: 14px;
        font-weight: 500;
        color: #64748b;
        margin-bottom: 5px;
    }
    
    .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
    }
    
    .analysis-section {
        background: white;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 30px;
    }
    
    .analysis-text {
        background-color: #f8fafc;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        border-left: 4px solid #2563eb;
        white-space: pre-line;
        line-height: 1.8;
    }
    
    .stButton > button {
        background-color: #2563eb;
        color: white;
        border: none;
        padding: 12px 25px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
    }
    
    .stButton > button:disabled {
        background-color: #94a3b8;
    }
    
    .stDownloadButton > button {
        background-color: white;
        color: #2563eb;
        border: 2px solid #e2e8f0;
        padding: 12px 25px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        border-color: #2563eb;
        transform: translateY(-2px);
    }
    
    .header h1 {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
    }
    
    .header p {
        color: #64748b;
        font-size: 16px;
    }
    
    .stSpinner > div {
        border: 5px solid #e2e8f0;
        border-top-color: #2563eb;
        border-radius: 50%;
        width: 60px;
        height: 60px;
    }
</style>
""", unsafe_allow_html=True)

def clean_text(text):
    """Rimuove caratteri non compatibili con il formato PDF standard"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    for i, pagina in enumerate(doc):
        if i > 30: break 
        t = pagina.get_text()
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except:
                t = "[Errore OCR]"
        testo_risultato += t
    return testo_risultato

# --- INTERFACCIA MIGLIORATA ---
# Sidebar con logo e dati economici
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">
            <i class="fas fa-shield-alt"></i>
        </div>
        <div class="logo-text">
            <h1>ASTA-SAFE AI</h1>
            <p>Valutatore Professionale</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2><i class="fas fa-euro-sign"></i> Dati Economici</h2>', unsafe_allow_html=True)
    prezzo_base = st.number_input("Base d'Asta (€)", value=100000, key="base_price")
    offerta_min = st.number_input("Offerta Minima (€)", value=75000, key="min_offer")
    
    st.markdown(f"""
    <div class="value-display">
        <p>Valore di partenza dell'asta</p>
        <h3>{prezzo_base:,.0f} €</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="value-display">
        <p>Valore minimo accettabile</p>
        <h3>{offerta_min:,.0f} €</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2><i class="fas fa-chart-line"></i> Benchmark Rischio</h2>', unsafe_allow_html=True)
    
    # Inizializza i benchmark
    if 'benchmarks' not in st.session_state:
        st.session_state.benchmarks = {
            'urbanistico': '-',
            'occupazione': '-', 
            'legale': '-',
            'economico': '-'
        }
    
    # Mostra i benchmark
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon urban">
                <i class="fas fa-building"></i>
            </div>
            <div class="stat-info">
                <h3>URBANISTICO</h3>
                <div class="stat-value">{}</div>
            </div>
        </div>
        """.format(st.session_state.benchmarks['urbanistico']), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon occupation">
                <i class="fas fa-house-user"></i>
            </div>
            <div class="stat-info">
                <h3>OCCUPAZIONE</h3>
                <div class="stat-value">{}</div>
            </div>
        </div>
        """.format(st.session_state.benchmarks['occupazione']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon legal">
                <i class="fas fa-gavel"></i>
            </div>
            <div class="stat-info">
                <h3>LEGALE</h3>
                <div class="stat-value">{}</div>
            </div>
        </div>
        """.format(st.session_state.benchmarks['legale']), unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon economic">
                <i class="fas fa-money-bill-wave"></i>
            </div>
            <div class="stat-info">
                <h3>ECONOMICO</h3>
                <div class="stat-value">{}</div>
            </div>
        </div>
        """.format(st.session_state.benchmarks['economico']), unsafe_allow_html=True)

# Area principale
st.markdown("""
<div class="header">
    <h1>Analisi Perizia CTU per Aste Giudiziarie</h1>
    <p>Carica un documento PDF per iniziare l'analisi AI dei rischi</p>
</div>
""", unsafe_allow_html=True)

# Sezione di caricamento
st.markdown("""
<div class="upload-section">
    <div class="upload-icon">
        <i class="fas fa-file-pdf"></i>
    </div>
    <h2>Carica Perizia CTU (PDF)</h2>
    <p>Trascina il file PDF della perizia tecnica oppure selezionalo dal tuo dispositivo.</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

if uploaded_file:
    st.success(f"✅ File caricato: {uploaded_file.name}")
    
    # Sezione di analisi
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown('<h2><i class="fas fa-chart-bar"></i> Esito dell\'Analisi</h2>', unsafe_allow_html=True)
    
    # Bottoni in colonne
    col1, col2 = st.columns([1, 2])
    
    with col1:
        download_placeholder = st.empty()
    
    with col2:
        if st.button("🚀 GENERA ANALISI BENCHMARK", use_container_width=True):
            try:
                with st.spinner("L'IA sta elaborando i dati..."):
                    # 1. Modello AI
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # 2. Estrazione
                    testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                    
                    # 3. Prompt
                    prompt = f"""
                    Analizza questa perizia per asta giudiziaria italiana. 
                    Genera questi BENCHMARK DI PERICOLOSITÀ (voto 1-10):
                    - URBANISTICO (Abusi/Sanabilità)
                    - OCCUPAZIONE (Stato immobile/Titoli)
                    - LEGALE (Vincoli/Servitù)
                    - ECONOMICO (Condominio/Sanzioni)
                    
                    IMPORTANTE: Rispondi SOLO con i 4 benchmark in questo formato esatto:
                    URBANISTICO: X/10
                    OCCUPAZIONE: X/10  
                    LEGALE: X/10
                    ECONOMICO: X/10
                    
                    Poi aggiungi una breve analisi di 3-4 righe.
                    
                    Testo: {testo_perizia[:15000]}
                    """
                    
                    response = model.generate_content(prompt)
                    analisi_testo = response.text
                    
                    # Estrai i voti dall'analisi
                    import re
                    voti = {}
                    for linea in analisi_testo.split('\n'):
                        if 'URBANISTICO:' in linea:
                            voti['urbanistico'] = linea.split(':')[1].strip()
                        elif 'OCCUPAZIONE:' in linea:
                            voti['occupazione'] = linea.split(':')[1].strip()
                        elif 'LEGALE:' in linea:
                            voti['legale'] = linea.split(':')[1].strip()
                        elif 'ECONOMICO:' in linea:
                            voti['economico'] = linea.split(':')[1].strip()
                    
                    # Aggiorna i benchmark nella sessione
                    for key in voti:
                        st.session_state.benchmarks[key] = voti[key]
                    
                    # 4. Risultati a Video
                    st.markdown(f"""
                    <div class="analysis-text">
                    {analisi_testo}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 5. Export PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    testo_pulito = clean_text(analisi_testo)
                    pdf.multi_cell(0, 10, txt=testo_pulito)
                    
                    pdf_output = pdf.output(dest='S')
                    pdf_bytes = bytes(pdf_output)
                    
                    # Mostra il pulsante download
                    download_placeholder.download_button(
                        label="📥 Scarica Report PDF",
                        data=pdf_bytes,
                        file_name="Analisi_Asta.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    # Ricarica la pagina per aggiornare i benchmark
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Errore: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Aggiungi Font Awesome per le icone
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)
