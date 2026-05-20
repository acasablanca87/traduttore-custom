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
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0 # Chiave per forzare lo svuotamento dell'allegato
if "modalita_radio" not in st.session_state:
    st.session_state.modalita_radio = None

def pulisci_chat():
    st.session_state.chat_history = []
    st.session_state.memo_contesto = ""
    st.session_state.uploader_key += 1 # Cambia la chiave, distrugge l'allegato precedente
    st.session_state.modalita_radio = None # Resetta anche la modalità, facendola tornare gialla

# Intestazione e Controlli
st.markdown(
    "<h4 style='margin-bottom: 0.5rem;'>Traduttore AI Logistica & Trasporti 🚛 "
    "<span style='font-size: 0.5em; font-weight: normal; color: #888;'>Powered by Gemini</span></h4>", 
    unsafe_allow_html=True
)

# --- Expander Istruzioni Rapide ---
with st.expander("ℹ️ Istruzioni rapide", expanded=False):
    st.markdown("""
    - **Modalità B2B/FIELD (obbligatoria):** prima di iniziare, devi scegliere il tono. *B2B* per comunicazioni formali (uffici, broker, clienti), *FIELD* per un linguaggio diretto e senza fronzoli (autisti, piazzale)
    - **Traduzione "Ping-Pong":** seleziona 1 sola volta a sessione la lingua di traduzione. Se scrivi in italiano, il sistema traduce in lingua straniera. Se scrivi in lingua straniera, traduce in italiano. Capisce da solo!
    """)

col_mod_label, col_mod_radio, col_lang, col_btn = st.columns([1, 1.5, 2, 2])

# Logica per l'evidenziatore giallo della Modalità
with col_mod_label:
    if st.session_state.modalita_radio is None:
        stile_dinamico = "background-color: yellow; color: black; padding: 4px 8px; border-radius: 5px;"
    else:
        stile_dinamico = "color: inherit; padding: 4px 0px;"
        
    st.markdown(f"<div style='margin-top: 5px; {stile_dinamico}'><b>Modalità:</b></div>", unsafe_allow_html=True)

with col_mod_radio:
    st.radio(
        "Modalità:", 
        ("🏢 B2B", "👷‍♂️ FIELD"), 
        horizontal=True, 
        label_visibility="collapsed",
        index=None,
        key="modalita_radio"
    )

with col_lang:
    lingue_disponibili = ["Francese", "Inglese", "Tedesco", "Spagnolo", "Rumeno", "Russo", "Polacco", "Ucraino", "Olandese", "Altro..."]
    
    # Capiamo cosa mostrare nel menu a tendina
    index_tendina = 0
    if st.session_state.lang_target in lingue_disponibili:
        index_tendina = lingue_disponibili.index(st.session_state.lang_target)
    else:
        index_tendina = lingue_disponibili.index("Altro...")
        
    scelta_lingua = st.selectbox("Lingua Straniera:", lingue_disponibili, index=index_tendina, label_visibility="collapsed")

with col_btn:
    st.button("♻️ Svuota chat e contesto", on_click=pulisci_chat, use_container_width=True)

# Se l'utente seleziona "Altro...", mostriamo il campo di testo per scrivere a mano
lingua_finale = st.session_state.lang_target
if scelta_lingua == "Altro...":
    lingua_custom = st.text_input("Scrivi la lingua desiderata (es. Portoghese):", value="" if st.session_state.lang_target in lingue_disponibili else st.session_state.lang_target)
    if lingua_custom:
        lingua_finale = lingua_custom.strip()
        st.session_state.lang_target = lingua_finale
else:
    lingua_finale = scelta_lingua
    st.session_state.lang_target = lingua_finale

# 5. GESTIONE DEL CONTESTO (Manuale o tramite PDF/Foto)
with st.expander("📝 Contesto", expanded=False):
    st.markdown("Scrivi dettagli sul carico o **carica un documento/foto** e lascia che l'IA estragga i dati chiave per migliorare la traduzione.")
    
    col_upload, col_text = st.columns([1, 2])
    with col_upload:
        file_caricato = st.file_uploader("Carica CMR (PDF) o Foto", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed", key=f"uploader_{st.session_state.uploader_key}")
        
        if st.button("🧠 Estrai contesto dagli allegati", use_container_width=True) and file_caricato:
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
    avatar_icon = "💬" if messaggio["role"] == "user" else "✨"
    with st.chat_message(messaggio["role"], avatar=avatar_icon):
        if messaggio["role"] == "assistant":
            st.code(messaggio["content"], language=None, wrap_lines=True)
        else:
            st.write(messaggio["content"])

# 6.5. MOSTRA IL CONTATORE DELLA MEMORIA
numero_messaggi = len(st.session_state.chat_history)
if numero_messaggi > 0:
    msg_in_memoria = min(numero_messaggi, 8)
    st.markdown(
        f"<div style='text-align: center; color: #888; font-size: 0.75rem; margin-top: 10px;'>"
        f"Memoria conversazione attiva (ultimi {msg_in_memoria} messaggi)</div>", 
        unsafe_allow_html=True
    )

# 7. INPUT UTENTE E CHIAMATA API (In basso nello schermo)
chat_disabilitata = st.session_state.modalita_radio is None
placeholder_testo = "Seleziona prima la Modalità (B2B o FIELD) in alto!" if chat_disabilitata else "Scrivi il messaggio da tradurre..."

user_input = st.chat_input(placeholder_testo, disabled=chat_disabilitata)

if user_input:
    # Mostra immediatamente il messaggio dell'utente
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="💬"):
        st.write(user_input)
        
    prompt_attivo = PROMPT_B2B if "B2B" in st.session_state.modalita_radio else PROMPT_FIELD
    
    # --- FIX DELLA LOGICA PING PONG ---
    istruzione_ping_pong = (
        f"🚨 REGOLA DI TRADUZIONE (MOLTO IMPORTANTE) 🚨\n"
        f"Fai da interprete bidirezionale tra due sole lingue: l'ITALIANO e il {lingua_finale.upper()}.\n"
        f"- Se il testo qui sotto è scritto in lingua ITALIANA, traduci in: {lingua_finale.upper()}.\n"
        f"- Se il testo qui sotto NON è in italiano (es. francese, inglese, tedesco, ecc.), traduci SEMPRE in: ITALIANO.\n"
        f"Non tradurre MAI in altre lingue e non fornire spiegazioni."
    )

    # Costruzione dello storico per Gemini
    testo_storia = ""
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
        
    comando_puro += f"{istruzione_ping_pong}\n\n[INPUT DA TRADURRE]:\n{user_input}"
    
    # Esegue la traduzione
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Traduzione..."):
            try:
                response = model.generate_content(f"{prompt_attivo}\n\n{comando_puro}")
                traduzione = response.text.strip()
                
                st.code(traduzione, language=None, wrap_lines=True)
                
                st.session_state.chat_history.append({"role": "assistant", "content": traduzione})
                st.rerun() # Forza il riavvio grafico pulito
            except Exception as e:
                st.error(f"Errore API Gemini: {e}")
