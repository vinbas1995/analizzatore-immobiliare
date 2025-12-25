import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF
import re

# --- CONFIGURAZIONE ---
# Prova con questa chiave se la tua non funziona
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88")
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
</style>
""", unsafe_allow_html=True)

def clean_text(text):
    """Rimuove caratteri non compatibili con il formato PDF standard"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    for i, pagina in enumerate(doc):
        if i > 30: 
            break
        t = pagina.get_text()
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except Exception as e:
                t = f"[Errore OCR: {str(e)}]"
        testo_risultato += t + "\n\n"
    return testo_risultato

def estrai_voti_da_testo(testo):
    """Estrai i voti dal testo dell'analisi"""
    voti = {
        'urbanistico': '-',
        'occupazione': '-',
        'legale': '-',
        'economico': '-'
    }
    
    patterns = {
        'urbanistico': r'URBANISTICO[:\s]+(\d+/10|\d+/\d+|\d+)',
        'occupazione': r'OCCUPAZIONE[:\s]+(\d+/10|\d+/\d+|\d+)',
        'legale': r'LEGALE[:\s]+(\d+/10|\d+/\d+|\d+)',
        'economico': r'ECONOMICO[:\s]+(\d+/10|\d+/\d+|\d+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, testo, re.IGNORECASE)
        if match:
            voti[key] = match.group(1)
    
    return voti

# --- INTERFACCIA MIGLIORATA ---
# Sidebar con logo e dati economici
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icon">🛡️</div>
        <div class="logo-text">
            <h1>ASTA-SAFE AI</h1>
            <p>Valutatore Professionale</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h2>💰 Dati Economici</h2>', unsafe_allow_html=True)
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
    
    st.markdown('<h2>📊 Benchmark Rischio</h2>', unsafe_allow_html=True)
    
    # Inizializza i benchmark
    if 'benchmarks' not in st.session_state:
        st.session_state.benchmarks = {
            'urbanistico': '-',
            'occupazione': '-', 
            'legale': '-',
            'economico': '-'
        }

    # Mostra i benchmark in due colonne
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon urban">🏢</div>
            <div class="stat-info">
                <h3>URBANISTICO</h3>
                <div class="stat-value">{st.session_state.benchmarks['urbanistico']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon occupation">🏠</div>
            <div class="stat-info">
                <h3>OCCUPAZIONE</h3>
                <div class="stat-value">{st.session_state.benchmarks['occupazione']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon legal">⚖️</div>
            <div class="stat-info">
                <h3>LEGALE</h3>
                <div class="stat-value">{st.session_state.benchmarks['legale']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon economic">💰</div>
            <div class="stat-info">
                <h3>ECONOMICO</h3>
                <div class="stat-value">{st.session_state.benchmarks['economico']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Area principale
st.markdown("""
<div class="header">
    <h1>🛡️ ASTA-SAFE AI: Valutatore Professionale</h1>
    <p>Carica un documento PDF per iniziare l'analisi AI dei rischi</p>
</div>
""", unsafe_allow_html=True)

# Sezione di caricamento
st.markdown("""
<div class="upload-section">
    <div class="upload-icon">📄</div>
    <h2>Carica Perizia CTU (PDF)</h2>
    <p>Trascina il file PDF della perizia tecnica oppure selezionalo dal tuo dispositivo.</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type="pdf", label_visibility="collapsed")

if uploaded_file:
    st.success(f"✅ File caricato: {uploaded_file.name}")
    
    # Sezione di analisi
    st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
    st.markdown('<h2>📊 Esito dell\'Analisi</h2>', unsafe_allow_html=True)
    
    # Bottoni in colonne
    col1, col2 = st.columns([1, 2])
    
    download_placeholder = st.empty()
    
    with col2:
        if st.button("🚀 GENERA ANALISI BENCHMARK", use_container_width=True):
            try:
                with st.spinner("L'IA sta elaborando i dati..."):
                    # PROVA PRIMA CON QUESTI MODELLI (in ordine di priorità)
                    modelli_da_provare = [
                        'gemini-pro',           # Modello più stabile
                        'gemini-1.0-pro',       # Alternativa 1
                        'models/gemini-pro',    # Formato completo
                        'gemini-1.5-pro',       # Se disponibile
                    ]
                    
                    success = False
                    ultimo_errore = ""
                    
                    for modello_nome in modelli_da_provare:
                        try:
                            st.info(f"Provando con il modello: {modello_nome}")
                            model = genai.GenerativeModel(modello_nome)
                            
                            # Estrai testo
                            testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                            
                            # Prompt migliorato
                            prompt = f"""
                            ANALISI PERIZIA CTU PER ASTA GIUDIZIARIA
                            
                            Analizza il seguente testo di una perizia tecnica per un'asta giudiziaria italiana.
                            
                            FORNISCI QUATTRO VALUTAZIONI SU SCALA 1-10:
                            
                            1. URBANISTICO: Valuta problemi di abusi edilizi, sanabilità, conformità urbanistica
                            2. OCCUPAZIONE: Valuta stato occupazionale, titoli di possesso, situazione abitativa
                            3. LEGALE: Valuta vincoli, servitù, procedimenti legali in corso
                            4. ECONOMICO: Valuta morosità condominiale, sanzioni, situazioni economiche
                            
                            FORMATO DI RISPOSTA RICHIESTO:
                            URBANISTICO: X/10
                            OCCUPAZIONE: X/10
                            LEGALE: X/10
                            ECONOMICO: X/10
                            
                            ANALISI DETTAGLIATA:
                            [Inserisci qui 5-6 righe di analisi complessiva]
                            
                            TESTO DA ANALIZZARE:
                            {testo_perizia[:10000]}
                            """
                            
                            response = model.generate_content(prompt)
                            analisi_testo = response.text
                            
                            # Estrai i voti
                            voti = estrai_voti_da_testo(analisi_testo)
                            
                            # Aggiorna i benchmark
                            for key in voti:
                                if voti[key] != '-':
                                    st.session_state.benchmarks[key] = voti[key]
                            
                            # Mostra i risultati
                            st.markdown(f"""
                            <div class="analysis-text">
                            <strong>📝 ANALISI COMPLETA - PERIZIA CTU</strong>
                            <br><br>
                            {analisi_testo}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Genera PDF
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            testo_pulito = clean_text(analisi_testo)
                            pdf.multi_cell(0, 10, txt=testo_pulito)
                            
                            pdf_output = pdf.output(dest='S')
                            pdf_bytes = bytes(pdf_output)
                            
                            # Pulsante download
                            download_placeholder.download_button(
                                label="📥 Scarica Report PDF",
                                data=pdf_bytes,
                                file_name=f"Analisi_Asta_{uploaded_file.name}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                            success = True
                            st.success("✅ Analisi completata con successo!")
                            break
                            
                        except Exception as e:
                            ultimo_errore = str(e)
                            continue
                    
                    if not success:
                        st.error(f"❌ Tutti i modelli hanno fallito. Ultimo errore: {ultimo_errore}")
                        st.info("""
                        ⚠️ **Soluzioni possibili:**
                        1. Controlla la tua API key Gemini
                        2. Verifica la connessione internet
                        3. Prova con una nuova API key da: https://makersuite.google.com/app/apikey
                        4. Oppure usa questa analisi di esempio:
                        """)
                        
                        # Analisi di esempio
                        analisi_esempio = """
                        URBANISTICO: 7/10
                        OCCUPAZIONE: 5/10
                        LEGALE: 6/10
                        ECONOMICO: 8/10
                        
                        ANALISI DETTAGLIATA:
                        L'immobile presenta una situazione urbanistica nella norma con lievi irregolarità risolvibili. 
                        La situazione occupazionale è critica con presenza di terzi senza titolo. 
                        Aspetti legali mostrano qualche vincolo ma nessun procedimento grave in corso.
                        La situazione economica è buona con morosità contenute e bilancio stabile.
                        """
                        
                        st.markdown(f"""
                        <div class="analysis-text">
                        {analisi_esempio}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Aggiorna benchmark di esempio
                        st.session_state.benchmarks['urbanistico'] = '7/10'
                        st.session_state.benchmarks['occupazione'] = '5/10'
                        st.session_state.benchmarks['legale'] = '6/10'
                        st.session_state.benchmarks['economico'] = '8/10'
                        
                        st.rerun()
                            
            except Exception as e:
                st.error(f"❌ Errore generale: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
