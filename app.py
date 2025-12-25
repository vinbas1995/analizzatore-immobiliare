import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import plotly.graph_objects as go

# --- CONFIGURAZIONE BRANDING ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

st.set_page_config(
    page_title="AstaSicura.it - Analisi Professionale",
    page_icon="⚖️",
    layout="wide"
)

# Custom CSS per stile istituzionale
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #d1d5db;
    }
    .report-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
        background-color: #0f172a;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def estrai_testo(file_pdf):
    doc = fitz.open(stream=file_pdf.read(), filetype="pdf")
    testo = ""
    for pagina in doc:
        testo += pagina.get_text()
    return testo

# --- INTERFACCIA ---
st.image("https://via.placeholder.com/250x60?text=ASTASICURA.IT", width=250) 
st.title("Sistema Certificato di Valutazione Asset")
st.markdown("---")

file_caricato = st.file_uploader("Carica Documentazione Tecnica (CTU)", type="pdf")

if file_caricato:
    if st.button("GENERA REPORT DI VALUTAZIONE"):
        try:
            with st.spinner("Elaborazione dati tecnici in corso..."):
                testo_perizia = estrai_testo(file_caricato)
                model = genai.GenerativeModel("gemini-1.5-flash")
                
                prompt = f"""
                Agisci come il dipartimento tecnico di AstaSicura.it. Analizza la perizia e restituisci un JSON con:
                - urbano (0-10), occupazione (0-10), legale (0-10), costi (0-10)
                - sintesi (stringa), raccomandazione (stringa)
                Testo: {testo_perizia[:25000]}
                """
                
                response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                dati = json.loads(response.text)

                # --- DASHBOARD ---
                st.subheader("📊 Analisi Multidimensionale del Rischio")
                
                col_metriche, col_grafico = st.columns([1, 1])

                with col_metriche:
                    st.metric("Rischio Urbanistico", f"{dati['urbano']}/10")
                    st.metric("Stato Occupativo", f"{dati['occupazione']}/10")
                    st.metric("Vincoli Giuridici", f"{dati['legale']}/10")
                    st.metric("Oneri Stimati", f"{dati['costi']}/10")

                with col_grafico:
                    # Grafico a Radar (Ragnatela)
                    categories = ['Urbanistico', 'Occupazione', 'Legale', 'Costi']
                    values = [dati['urbano'], dati['occupazione'], dati['legale'], dati['costi']]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatterpolar(
                        r=values + [values[0]],
                        theta=categories + [categories[0]],
                        fill='toself',
                        fillcolor='rgba(15, 23, 42, 0.3)',
                        line=dict(color='#0f172a', width=2)
                    ))

                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 10])
                        ),
                        showlegend=False,
                        margin=dict(l=40, r=40, t=20, b=20),
                        height=350
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown(f"""
                <div class="report-card">
                    <h4>📝 Parere Professionale AstaSicura.it</h4>
                    <p>{dati['sintesi']}</p>
                    <hr>
                    <strong>Raccomandazione Strategica:</strong> {dati['raccomandazione']}
                </div>
                """, unsafe_allow_html=True)
                
                st.download_button("Scarica Report Certificato", "Dati analisi...", file_name="report_astasicura.txt")

        except Exception as e:
            st.error("Errore di sistema. Verificare l'integrità del file PDF.")
