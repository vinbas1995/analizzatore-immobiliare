import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import plotly.graph_objects as go

# --- CONFIGURAZIONE PRIVACY E BRANDING ---
# Assicurati di avere GEMINI_API_KEY nei Secrets di Streamlit
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="AstaSicura.it | Portale Analisi Tecnica",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS CUSTOM PER LOOK PROFESSIONALE ---
st.markdown("""
    <style>
    /* Sfondo e Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    
    /* Header Personalizzato */
    .nav-bar {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 0 0 15px 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Card Risultati */
    .report-card {
        background-color: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-top: 20px;
    }
    
    /* Metriche High-End */
    div[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 600 !important; color: #1e293b !important; }
    div[data-testid="stMetric"] {
        background: white;
        padding: 20px !important;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }

    /* Nascondi Elementi Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Bottoni Custom */
    .stButton>button {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

def estrai_testo(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo = ""
    for pagina in doc:
        testo += pagina.get_text()
    return testo

# --- HEADER WEB ---
st.markdown("""
    <div class="nav-bar">
        <h1 style='margin:0; font-size: 24px; letter-spacing: 1px;'>ASTASICURA.IT</h1>
        <p style='margin:0; opacity: 0.8; font-size: 14px;'>SISTEMA DI AUDIT TECNICO-GIUDIZIARIO CERTIFICATO</p>
    </div>
    """, unsafe_allow_html=True)

# --- SEZIONE CARICAMENTO ---
col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown("### 📄 Caricamento Documentazione")
    file_caricato = st.file_uploader("Trascina qui la Perizia CTU in formato PDF", type="pdf", label_visibility="collapsed")

with col_r:
    st.markdown("### ℹ️ Istruzioni")
    st.caption("Il sistema analizza i dati estratti dalla perizia per calcolare l'indice di pericolosità dell'investimento secondo i protocolli di AstaSicura.it.")

if file_caricato:
    if st.button("ESEGUI ANALISI PROFESSIONALE"):
        try:
            with st.spinner("Accesso ai database documentali e calcolo indici in corso..."):
                testo_perizia = estrai_testo(file_caricato)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                Agisci come il dipartimento di analisi rischi di AstaSicura.it. Analizza questa perizia e restituisci un JSON:
                - urbano, occupazione, legale, costi (tutti interi 0-10)
                - sintesi_direzionale (max 150 parole)
                - criticita_rilevate (lista di 3 punti)
                - verdetto_finale (stringa breve)
                Testo: {testo_perizia[:28000]}
                """
                
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                dati = json.loads(response.text)

                # --- DASHBOARD RISULTATI ---
                st.markdown("---")
                st.markdown("## 📊 Risultanze dell'Audit")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Urbanistico", f"{dati['urbano']}/10")
                m2.metric("Occupazione", f"{dati['occupazione']}/10")
                m3.metric("Titoli Legali", f"{dati['legale']}/10")
                m4.metric("Oneri Occulti", f"{dati['costi']}/10")

                # --- GRAFICO E SINTESI ---
                col_chart, col_text = st.columns([1, 1])

                with col_chart:
                    categories = ['Urbanistico', 'Occupazione', 'Legale', 'Costi']
                    values = [dati['urbano'], dati['occupazione'], dati['legale'], dati['costi']]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        fillcolor='rgba(59, 130, 246, 0.2)',
                        line=dict(color='#1e3a8a', width=3)
                    ))
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#e2e8f0")),
                        showlegend=False,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col_text:
                    st.markdown(f"""
                    <div class="report-card">
                        <h4 style='color:#1e3a8a; margin-top:0;'>📝 Sintesi Direzionale</h4>
                        <p style='font-size: 15px; line-height: 1.6;'>{dati['sintesi_direzionale']}</p>
                        <h4 style='color:#1e3a8a;'>⚠️ Criticità Evidenziate</h4>
                        <ul style='font-size: 14px;'>
                            <li>{"</li><li>".join(dati['criticita_rilevate'])}</li>
                        </ul>
                        <div style='background:#f1f5f9; padding:15px; border-radius:8px; border-left:4px solid #1e3a8a;'>
                            <strong>Verdetto AstaSicura:</strong> {dati['verdetto_finale']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # --- FOOTER AZIONI ---
                st.markdown("<br>", unsafe_allow_html=True)
                c_down1, c_down2, c_down3 = st.columns([1, 1, 1])
                with c_down2:
                    st.button("📥 SCARICA REPORT CERTIFICATO (PDF)")

        except Exception as e:
            st.error("Il sistema non è riuscito a processare il documento. Verificare che il PDF non sia protetto da password.")

# --- FOOTER PAGINA ---
st.markdown("""
    <div style='text-align:center; padding:40px; color:#94a3b8; font-size:12px;'>
        AstaSicura.it © 2024 - Servizio di Analisi per Investitori Professionali<br>
        Le valutazioni hanno scopo puramente informativo basato sui dati estratti.
    </div>
    """, unsafe_allow_html=True)
