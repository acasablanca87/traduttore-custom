import streamlit as st
import google.generativeai as genai
from PIL import Image
from prompts import PROMPT_FIELD, PROMPT_B2B

# 1. Configurazione della pagina
st.set_page_config(page_title="Traduttore Logistico AI", page_icon="🚛", layout="centered")

# CSS per ottimizzare gli spazi
st.markdown("""
    <style>
        .block-container { padding-top: 2rem !important; }
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
        pass_admin = st.secrets.get("PASS_ADMIN", "")
        pass_colleghi = st.secrets.get("PASS_COLLEGHI", "")
        
        if password and (password == pass_admin or password == pass_colleghi):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Password errata.")
    return False

if not check_password():
    st.stop()

# --- APP VERA E PROPRIA INIZIA QUI ---

# 3. Configurazione API e Modello
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-3.1-flash-lite')

# 4. Inizializzazione Memoria Sessione
if "lang_target" not in st.session_state:
    st.session_state.lang_target = "Francese"
if "memo_contesto" not in st.session_state:
    st.session_state.memo_contesto = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def pulisci_chat():
    st.session_state.chat_history = []
    st.session_state.memo_contesto = ""

# Intestazione e Controlli
st.markdown(
    "<h4 style='margin-bottom: 0.5rem;'>Traduttore AI Logistica & Trasporti 🚛 "
    "<span style='font-size: 0.5em; font-weight: normal; color: #888;'>Powered by Gemini</span></h4>", 
    unsafe_allow_html=True
)

col_mod, col_lang, col_btn = st.columns([2, 2, 1.5])
with col_mod:
    modalita = st.radio("Modalità:", ("🏢 B2B", "👷‍♂️ FIELD"), horizontal=True, label_visibility="collapsed")
with col_lang:
    lingue_disponibili = ["Francese", "Inglese", "Tedesco", "Spagnolo", "Rumeno", "Russo", "Polacco", "Ucraino", "Olandese"]
    st.session_state.lang_target = st.selectbox("Lingua Straniera:", lingue_disponibili, index=lingue_disponibili.index(st.session_state.lang_target), label_visibility="collapsed")
with col_btn:
    st.button("🗑️ Svuota Chat", on_click=pulisci_chat, use_container_width=True)

# 5. GESTIONE DEL CONTESTO (Manuale o tramite PDF/Foto)
with st.expander("📂 Contesto della Spedizione (CMR o Note)", expanded=False):
    st.markdown("Scrivi dettagli sul carico o **carica un documento/foto** e lascia che l'IA estragga i dati chiave per migliorare la traduzione.")
    
    col_upload, col_text = st.columns([1, 2])
    with col_upload:
        file_caricato = st.file_uploader("Carica CMR (PDF) o Foto", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")
        if st.button("🧠 Estrai Contesto", use_container_width=True) and file_caricato:
            with st.spinner("Analisi documento in corso..."):
                try:
                    payload = ["Analizza questo documento logistico e scrivi un riassunto di massimo 2 righe con le informazioni utili per una traduzione (es. merce, destinazione, targa). Restituisci SOLO il riassunto, senza preamboli."]
                    if file_caricato.type == "application/pdf":
                        payload.append({"mime_type": "application/pdf", "data": file_caricato.getvalue()})
                    else:
                        img = Image.open(file_caricato)
                        payload.append(img)
                    
                    response_contesto = model.generate_content(payload)
                    st.session_state.memo_contesto = response_contesto.text.strip()
                    st.success("Contesto aggiornato!")
                except Exception as e:
                    st.error(f"Errore analisi: {e}")

    with col_text:
        st.session_state.memo_contesto = st.text_area(
            "Note di contesto attuali:", 
            value=st.session_state.memo_contesto, 
            height=100,
            label_visibility="collapsed",
            placeholder="Es. Camion frigo diretto a Milano, scarico ritardato."
        )

st.divider()

# 6. MOSTRA LO STORICO DELLA CHAT
for messaggio in st.session_state.chat_history:
    avatar_icon = "👤" if messaggio["role"] == "user" else "🤖"
    with st.chat_message(messaggio["role"], avatar=avatar_icon):
        st.write(messaggio["content"])

# 7. INPUT UTENTE E CHIAMATA API (In basso nello schermo)
user_input = st.chat_input("Scrivi il messaggio da tradurre (In italiano o lingua straniera)...")

if user_input:
    # Mostra immediatamente il messaggio dell'utente
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.write(user_input)
        
    prompt_attivo = PROMPT_B2B if "B2B" in modalita else PROMPT_FIELD
    lingua = st.session_state.lang_target
    
    # Costruzione logica Ping Pong
    istruzione_ping_pong = (
        f"🚨 [REGOLA DI TRADUZIONE OBBLIGATORIA - PING PONG] 🚨\n"
        f"1. Analizza la lingua dell'[INPUT] fornito qui sotto.\n"
        f"2. Se l'[INPUT] è in ITALIANO -> TRADUCI IN {lingua.upper()}.\n"
        f"3. Se l'[INPUT] NON È in ITALIANO -> TRADUCI IN ITALIANO.\n"
        f"⚠️ DIVIETO ASSOLUTO: È severamente vietato rispondere nella stessa lingua dell'input."
    )

    # Costruzione dello storico per Gemini
    testo_storia = ""
    # Prendiamo gli ultimi 8 messaggi scambiati per dare memoria senza esaurire i token
    for m in st.session_state.chat_history[-9:-1]: 
        ruolo = "Originale" if m["role"] == "user" else "Traduzione"
        testo_storia += f"{ruolo}: {m['content']}\n"

    comando_puro = ""
    if st.session_state.memo_contesto.strip():
        comando_puro += f"📌 [CONTESTO DEL TRASPORTO ATTUALE]:\n{st.session_state.memo_contesto}\n\n"
        
    if testo_storia:
        comando_puro += (
            f"🕒 [STORICO RECENTE DELLA CONVERSAZIONE]:\n{testo_storia}\n"
            f"⚠️ Usa lo storico solo per capire il contesto o a cosa si riferisce l'utente.\n\n"
        )
        
    comando_puro += f"{istruzione_ping_pong}\n\n[INPUT]:\n{user_input}"
    
    # Esegue la traduzione
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Traduzione..."):
            try:
                response = model.generate_content(f"{prompt_attivo}\n\n{comando_puro}")
                traduzione = response.text.strip()
                st.write(traduzione)
                
                # Salva la risposta nello storico
                st.session_state.chat_history.append({"role": "assistant", "content": traduzione})
            except Exception as e:
                st.error(f"Errore API Gemini: {e}")
