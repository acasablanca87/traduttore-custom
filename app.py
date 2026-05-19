import streamlit as st
import google.generativeai as genai
from PIL import Image
from prompts import PROMPT_FIELD, PROMPT_B2B

# 1. Configurazione della pagina
st.set_page_config(page_title="Traduttore Logistico AI", page_icon="🚛", layout="wide")

# CSS per ottimizzare gli spazi
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; }
        div[data-testid="stCodeBlock"] button { right: auto !important; left: 0.5rem !important; }
        div[data-testid="stCodeBlock"] pre { padding-left: 3.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# 2. SISTEMA DI LOGIN (Security Wall)
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.markdown("### 🔒 Accesso Riservato")
    password = st.text_input("Inserisci la password operativa:", type="password")
    
    if st.button("Accedi"):
        # Leggiamo le password dai secrets di Streamlit
        pass_admin = st.secrets.get("PASS_ADMIN", "")
        pass_colleghi = st.secrets.get("PASS_COLLEGHI", "")
        
        if password and (password == pass_admin or password == pass_colleghi):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Password errata.")
    return False

# Blocca l'esecuzione se non sei loggato
if not check_password():
    st.stop()

# --- APP VERA E PROPRIA INIZIA QUI ---

# Intestazione
st.markdown(
    "<h4 style='margin-bottom: 0.5rem;'>Traduttore AI Logistica & Trasporti 🚛 "
    "<span style='font-size: 0.5em; font-weight: normal; color: #888;'>Powered by Gemini</span></h4>", 
    unsafe_allow_html=True
)

# 3. Configurazione API e Modello
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.1-flash-lite') # Usiamo lo stesso modello veloce del Bot

# 4. Inizializzazione Memoria Sessione
if "lang_target" not in st.session_state:
    st.session_state.lang_target = "Francese"
if "testo_tradotto" not in st.session_state:
    st.session_state.testo_tradotto = ""
if "memo_contesto" not in st.session_state:
    st.session_state.memo_contesto = ""

def pulisci_chat():
    st.session_state.testo_tradotto = ""
    st.session_state.memo_contesto = ""

# 5. UI: Selezione Modalità
modalita = st.radio(
    "Modalità di Traduzione:",
    ("🏢 B2B (Uffici, Broker e Clienti)", "👷‍♂️ FIELD (Autisti e Magazzino)"),
    horizontal=True
)

st.divider()

# 6. GESTIONE DEL CONTESTO (Manuale o tramite PDF/Foto)
with st.expander("📂 Contesto della Spedizione (Opzionale)", expanded=False):
    st.markdown("Scrivi qui i dettagli del carico o **carica un documento/foto** e lascia che l'IA lo analizzi per te.")
    
    col_upload, col_text = st.columns([1, 2])
    
    with col_upload:
        file_caricato = st.file_uploader("Carica CMR, Ordine (PDF) o Foto", type=["pdf", "png", "jpg", "jpeg"])
        if st.button("🧠 Estrai Contesto dal File", use_container_width=True) and file_caricato:
            with st.spinner("Analisi documento..."):
                try:
                    payload = ["Analizza questo documento logistico e scrivi un riassunto di massimo 2 righe con le informazioni utili per una traduzione (es. merce, destinazione, targa). Restituisci SOLO il riassunto."]
                    if file_caricato.type == "application/pdf":
                        payload.append({"mime_type": "application/pdf", "data": file_caricato.getvalue()})
                    else:
                        img = Image.open(file_caricato)
                        payload.append(img)
                    
                    response_contesto = model.generate_content(payload)
                    st.session_state.memo_contesto = response_contesto.text.strip()
                    st.success("Contesto estratto!")
                except Exception as e:
                    st.error(f"Errore analisi: {e}")

    with col_text:
        st.session_state.memo_contesto = st.text_area(
            "Note di contesto attuali:", 
            value=st.session_state.memo_contesto, 
            height=100
        )

# 7. LOGICA TRADUZIONE (Ping Pong Integrato)
col_lingua, col_spazio = st.columns([1, 3])
with col_lingua:
    lingue_disponibili = ["Francese", "Inglese", "Tedesco", "Spagnolo", "Rumeno", "Russo", "Polacco", "Ucraino", "Olandese"]
    st.session_state.lang_target = st.selectbox("Lingua Straniera:", lingue_disponibili, index=lingue_disponibili.index(st.session_state.lang_target))

col_input, col_output = st.columns(2)

with col_input:
    with st.form(key="form_traduzione", border=False):
        testo_da_tradurre = st.text_area(
            "Messaggio da tradurre:", 
            height=200, 
            placeholder="Scrivi in italiano per tradurre in lingua straniera.\nScrivi in lingua straniera per tradurre in italiano.\nL'IA capirà da sola."
        )
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            btn_traduci = st.form_submit_button("Traduci", type="primary", use_container_width=True)
        with col_btn2:
            st.form_submit_button("Svuota Traduzione", on_click=pulisci_chat, use_container_width=True)

with col_output:
    if st.session_state.testo_tradotto:
        st.markdown("**Risultato:**")
        st.code(st.session_state.testo_tradotto, language=None, wrap_lines=True)
    else:
        st.info("La traduzione apparirà qui.")

# 8. ESECUZIONE TRADUZIONE
if btn_traduci and testo_da_tradurre.strip():
    prompt_attivo = PROMPT_B2B if "B2B" in modalita else PROMPT_FIELD
    lingua = st.session_state.lang_target
    
    # Costruzione logica Ping Pong
    istruzione_ping_pong = (
        f"🚨 [REGOLA DI TRADUZIONE OBBLIGATORIA - PING PONG] 🚨\n"
        f"1. Analizza la lingua dell'[INPUT] fornito qui sotto.\n"
        f"2. Se l'[INPUT] è in ITALIANO -> TRADUCI IN {lingua.upper()}.\n"
        f"3. Se l'[INPUT] NON È in ITALIANO -> TRADUCI IN ITALIANO.\n"
        f"⚠️ Se l'input è brevissimo (es. 'ok', 'yes'), TRADUCILO SEMPRE.\n"
        f"DIVIETO ASSOLUTO: È severamente vietato rispondere nella stessa lingua dell'input."
    )

    comando_puro = ""
    if st.session_state.memo_contesto.strip():
        comando_puro += f"📌 [CONTESTO DEL TRASPORTO ATTUALE]:\n{st.session_state.memo_contesto}\n\n"
        
    comando_puro += f"{istruzione_ping_pong}\n\n[INPUT]:\n{testo_da_tradurre}"
    
    with st.spinner("Traduzione in corso... ⏳"):
        try:
            response = model.generate_content(f"{prompt_attivo}\n\n{comando_puro}")
            st.session_state.testo_tradotto = response.text.strip()
            st.rerun() # Ricarica per mostrare il risultato
        except Exception as e:
            st.error(f"Errore API Gemini: {e}")
