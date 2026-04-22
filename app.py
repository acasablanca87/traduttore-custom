import streamlit as st
import google.generativeai as genai

# Configurazione grafica della pagina
st.set_page_config(page_title="Il mio Traduttore Custom", page_icon="🌍")

st.title("🌍 Traduttore Contestuale con Gemini")
st.markdown("Inserisci il contesto e il testo da tradurre.")

# Recupera la API Key in modo sicuro da Streamlit
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# Inizializza il modello (gemini-1.5-flash è veloce e ottimo per testi)
model = genai.GenerativeModel('gemini-3.1-pro-preview')

# Box per inserire il Contesto (le tue regole)
contesto = st.text_area(
    "Parametri di contesto e regole di traduzione:",
    value="Agisci come un traduttore esperto. Traduci il testo seguente in italiano. Usa un tono formale, mantieni i termini tecnici in lingua originale e assicurati che la frase scorra in modo naturale."
)

# Box per inserire il testo vero e proprio
testo_da_tradurre = st.text_area("Testo da tradurre:")

# Bottone di azione
if st.button("Traduci"):
    if testo_da_tradurre:
        with st.spinner("Traduzione in corso..."):
            # Uniamo le tue regole al testo da tradurre
            prompt_completo = f"{contesto}\n\nEcco il testo da tradurre:\n{testo_da_tradurre}"
            
            try:
                # Chiamata alle API di Gemini
                response = model.generate_content(prompt_completo)
                st.success("Fatto!")
                st.write(response.text)
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
    else:
        st.warning("Inserisci del testo da tradurre prima di cliccare!")
