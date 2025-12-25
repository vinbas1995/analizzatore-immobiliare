import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import google.generativeai as genai
from fpdf import FPDF

# --- 1. CONFIGURAZIONE PAGINA E STILE ---
st.set_page_config(
    page_title="ASTA-SAFE AI | Analisi Immobiliare Pro",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizzato per look professionale (Stile Enterprise)
st.markdown("""
    <style>
    /* Colori e Font */
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
    }
    h2, h3 {
        color: #34495e;
    }
    
    /* Stile Banner Pubblicitari */
    .ad-container {
        background-color: #e9ecef;
        border: 2px dashed #adb5bd;
        color: #6c757d;
        text-align: center;
        padding: 20px;
        margin: 15px 0;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    /* Card per i risultati */
    .result-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #2ecc71;
    }
    
    /* Bottone Personalizzato */
    .stButton>button {
        background-color: #2980b9;
        color: white;
        border-radius: 5px;
        height: 3em;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1a5276;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SETUP API ---
# Chiave API inserita direttamente nel codice
GEMINI_API_KEY = "AIzaSyDIgbUDRHLRPX0A4XdrTbaj7HF6zuCSj88"
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. FUNZIONI DI UTILITÀ ---

def render_ad_space(position_name, height="100px"):
    """Funzione per inserire spazi pubblicitari HTML"""
    # In produzione, sostituisci questo HTML con lo script di Google Adsense
    html_code = f"""
    <div class="ad-container" style="height: {height}; display: flex; align-items: center; justify-content: center;">
        <div>
            SPAZIO PUBBLICITARIO - {position_name}<br>
            <small>(Inserisci qui il codice AdSense/Banner)</small>
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

def clean_text(text):
    """Pulisce il testo per evitare errori nel PDF"""
    return text.encode('latin-1', 'replace').decode('latin-1')

def estrai_testo_ottimizzato(file_pdf):
    """Estrae testo da PDF ibridi (Testo + Immagini)"""
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo_risultato = ""
    
    # Progress bar visuale per l'utente
    progress_bar = st.progress(0)
    total_pages = min(len(doc), 30) # Analizza max 30 pagine per velocità
    
    for i, pagina in enumerate(doc):
        if i >= 30: break 
        
        # Aggiorna barra progresso
        progress_bar.progress((i + 1) / total_pages)
        
        t = pagina.get_text()
        # Se c'è poco testo, prova OCR (utile per perizie scansionate male)
        if len(t) < 150: 
            try:
                pix = pagina.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                img = Image.open(io.BytesIO(pix.tobytes()))
                t = pytesseract.image_to_string(img, lang='ita')
            except:
                t = " [Testo non leggibile in questa pagina] "
        testo_risultato += t
        
    progress_bar.empty() # Rimuovi barra alla fine
    return testo_risultato

# --- 4. LAYOUT SIDEBAR ---
with st.sidebar:
    # Logo fittizio
    st.image("https://cdn-icons-png.flaticon.com/512/2642/2642232.png", width=60)
    st.markdown("### 🛡️ ASTA-SAFE Config")
    st.markdown("---")
    
    st.markdown("#### 💰 Parametri Economici")
    prezzo_base = st.number_input("Base d'Asta (€)", value=100000, step=1000, format="%d")
    offerta_min = st.number_input("Offerta Minima (€)", value=75000, step=1000, format="%d")
    
    st.markdown("---")
    
    # --- BANNER SIDEBAR ---
    render_ad_space("BANNER SIDEBAR (Verticale)", height="300px")
    
    st.info("💡 Suggerimento: Carica file PDF < 20MB per prestazioni ottimali.")
    st.caption("© 2024 ASTA-SAFE AI Pro")

# --- 5. LAYOUT PRINCIPALE ---

# Header
st.title("🛡️ ASTA-SAFE AI")
st.subheader("Analisi Intelligente Perizie Immobiliari")
st.markdown("Carica la perizia CTU e ottieni in pochi secondi un'analisi dei rischi legali, urbanistici ed economici.")

# --- BANNER TOP ---
render_ad_space("BANNER TOP (Orizzontale)", height="90px")

# Area di Upload
st.markdown("### 📂 Caricamento Documentazione")
uploaded_file = st.file_uploader("", type="pdf", help="Trascina qui la perizia ufficiale")

if uploaded_file:
    # Layout a due colonne per il pulsante
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("") # Spaziatura
        st.write("") 
        analyze_btn = st.button("🚀 AVVIA ANALISI COMPLETA")
    with col2:
        st.write("")
        if analyze_btn:
             st.success("File ricevuto. Elaborazione in corso...")

    if analyze_btn:
        try:
            with st.spinner("🕵️‍♂️ L'IA sta leggendo la perizia (OCR + Analisi Semantica)..."):
                
                # 1. Selezione Modello Dinamica
                available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                modello_scelto = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
                model = genai.GenerativeModel(modello_scelto)
                
                # 2. Estrazione Testo
                uploaded_file.seek(0) # Reset puntatore file
                testo_perizia = estrai_testo_ottimizzato(uploaded_file)
                
                # Controllo se il testo è vuoto
                if len(testo_perizia) < 50:
                    st.error("Non sono riuscito a leggere il testo. Il PDF potrebbe essere un'immagine scannerizzata di bassa qualità.")
                    st.stop()

                # 3. Prompt Strategico per l'AI
                prompt = f"""
                Agisci come un esperto consulente legale e immobiliare per aste giudiziarie italiane.
                Analizza il testo estratto dalla perizia seguente.
                
                Genera un REPORT STRUTTURATO in Markdown con le seguenti sezioni:
                
                1. **🚦 RATING DI RISCHIO (Tabella riassuntiva)**
                   - Assegna un voto da 1 (Critico) a 10 (Sicuro) per: Urbanistica, Stato Occupativo, Vincoli Legali, Costi Occulti.
                
                2. **⚠️ CRITICITÀ RILEVATE (Elenco puntato dettagliato)**
                   - Evidenzia abusi non sanabili, inquilini con titolo opponibile, diritti di terzi, discrepanze catastali.
                
                3. **💰 ANALISI ECONOMICA**
                   - Confronto Base d'Asta (€{prezzo_base}) vs Valore stimato (cerca nel testo).
                   - Costi stimati per sanatorie o spese condominiali arretrate (se citate).
                
                4. **🏁 CONCLUSIONE DELL'ESPERTO**
                   - Giudizio sintetico: "Affare", "Da Valutare con cautela" o "Sconsigliato".
                
                Testo Perizia (estratto): {testo_perizia[:25000]}
                """
                
                response = model.generate_content(prompt)
                analisi_testo = response.text

                # 4. Visualizzazione Risultati
                st.markdown("---")
                
                # Container stilizzato per il risultato
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown("## 📊 Risultato Analisi")
                st.markdown(analisi_testo)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # --- BANNER MIDDLE (Tra analisi e download) ---
                st.write("")
                render_ad_space("BANNER IN-CONTENT", height="90px")
                
                # 5. Export PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                # Intestazione PDF
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Report Analisi ASTA-SAFE AI", 0, 1, 'C')
                pdf.ln(10)
                
                # Corpo PDF
                pdf.set_font("Arial", size=11)
                # Pulizia caratteri speciali Markdown per il PDF
                testo_pdf = clean_text(analisi_testo.replace("**", "").replace("##", "").replace("#", ""))
                pdf.multi_cell(0, 8, txt=testo_pdf)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                st.write("")
                st.download_button(
                    label="📥 Scarica Report Ufficiale (PDF)", 
                    data=pdf_bytes, 
                    file_name="Analisi_Asta_Pro.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Si è verificato un errore durante l'analisi: {e}")

# --- BANNER FOOTER ---
st.markdown("---")
render_ad_space("BANNER FOOTER", height="120px")

# Footer Legale
st.markdown("""
<div style="text-align: center; color: #7f8c8d; font-size: 0.8em; margin-top: 20px;">
    AVVISO: Questo strumento utilizza Intelligenza Artificiale per supportare l'analisi ma non sostituisce il parere di un professionista.<br>
    Verificare sempre la documentazione ufficiale sul Portale Vendite Pubbliche.
</div>
""", unsafe_allow_html=True)
