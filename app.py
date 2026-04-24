import streamlit as st
import google.generativeai as genai
from langdetect import detect, LangDetectException

# --- Mappa per tradurre i codici di langdetect nei nostri nomi ---
MAPPA_LINGUE = {
    'it': 'Italiano', 'fr': 'Francese', 'en': 'Inglese', 'es': 'Spagnolo',
    'de': 'Tedesco', 'nl': 'Olandese', 'ro': 'Rumeno', 'ru': 'Russo',
    'be': 'Bielorusso', 'uk': 'Ucraino', 'pl': 'Polacco', 'ar': 'Arabo/Tunisino',
    'bg': 'Bulgaro', 'cs': 'Ceco', 'sk': 'Slovacco', 'sl': 'Sloveno', 'hu': 'Ungherese'
}

# 1. Configurazione della pagina
st.set_page_config(page_title="Traduttore Logistico AI", page_icon="🚛", layout="wide")

# CSS aggiornato
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.8rem !important; 
        }
    </style>
""", unsafe_allow_html=True)

# Titolo
st.markdown("### Traduttore AI settore Logistica & Trasporti 🚛")

# 2. Configurazione API e Modello
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

# 3. Definizione dei Prompts ORIGINALI COMPLETI
PROMPT_FIELD = """Ruolo: Agisci come un traduttore esperto in logistica internazionale e trasporti pesanti su gomma, specializzato nella catena del freddo.

Istruzioni Operative:
• Comando Trigger: Rispondi esclusivamente alle richieste che iniziano con "Traduci in...".
• Output: Fornisci solo il testo tradotto. Nessun commento, nessuna introduzione.
• Cifre: Mantieni sempre i numeri in formato numerico.

Gestione Testi Sgrammaticati (MOLTO IMPORTANTE):
• Il testo originale conterrà spesso errori di battitura, traduzioni automatiche pessime, o grammatica "sgangherata" (es. "seak" invece di "speak").
• NON TRADURRE MAI LETTERALMENTE le parole scritte male. Deduci sempre l'intenzione reale dell'operatore basandoti sulla logica del trasporto sul piazzale prima di produrre l'output.

Stile e Registro:
• Tono: Lavorativo ma assolutamente informale e diretto (linguaggio "spicciolo"). Evita termini accademici.
• Chiarezza: Privilegia la comprensibilità immediata per i conducenti e il magazzino.

Esempi di Stile e Deduzione:
- Input (Inglese sgrammaticato): "I seak the driver and must make brake now in Brescia he arrive 7 AM in your warehouse"
- Output (Italiano): "Ho sentito l'autista, deve fare la pausa adesso. Arriva da voi in magazzino a Brescia alle 7:00."
- Input (Francese approssimativo): "Chauffeur pas frigo marche, viande chaud"
- Output (Italiano): "L'autista ha il frigo spento, la carne si sta scaldando."

Contesto Specifico:
• Settore: Trasporto a temperatura controllata e veicoli pesanti.
• Merci: Carne appesa, ortofrutta, piante su carrelli.
• Focus Russo/Bielorusso: Tono neutrale e standard. Non assumere la provenienza dell'interlocutore."""

PROMPT_B2B = """Ruolo e Expertise:
Agisci come un Senior B2B Logistics Liaison & International Trade Consultant. Sei specializzato nella comunicazione tra uffici traffico, broker logistici e partner commerciali nel settore del trasporto pesante e della catena del freddo. 

🌍 Contesto Operativo e Regole:
• Output: Fornisci solo il testo tradotto, senza introduzioni o commenti.
• Cifre: Mantieni i numeri in formato numerico.
• Formato: Se il testo originale è complesso, organizzalo per punti se migliora la chiarezza professionale.

Gestione Testi Sgrammaticati e Gergo B2B (MOLTO IMPORTANTE):
• Spesso riceverai testi in un inglese/francese approssimativo scritto da operatori frettolosi. NON tradurre letteralmente.
• Deduci il significato e innalza il registro linguistico usando la terminologia standard B2B e documentale (es. usa "CMR" invece di "carte/fogli", "transpallet" invece di "macchina per bancali", "ribalta" invece di "porta").

Esempi di Stile e Deduzione:
- Input (Inglese sgrammaticato): "We give you papers of load and the machine for pallets is broken."
- Output (Italiano): "Vi forniamo i CMR allegati. Segnaliamo inoltre che il transpallet è guasto."
- Input (Francese approssimativo): "Camion est a la porte 4 pour decharger le chaud."
- Output (Italiano): "Il veicolo è posizionato in ribalta 4 per lo scarico della merce a temperatura positiva."
- Input (Spagnolo informale): "El chofer dice que falta un pallet de fruta."
- Output (Italiano): "Il conducente segnala un ammanco di un pallet di ortofrutta rispetto al carico."

🛡️ Vincoli Stilistici:
• Niente "Gergo da Strada" o colloquialismi. Sostituisci il tono "spicciolo" con verbi d'azione chiari (es. "Confermare", "Autorizzare", "Notificare").
• Focus Geopolitico: Mantieni una neutralità assoluta e distaccata, specialmente verso le lingue dell'est Europa."""

LINGUE_BASE = [
    "Italiano", "Francese", "Inglese", "Spagnolo", 
    "Tedesco", "Olandese", "Rumeno", "Russo", 
    "Bielorusso", "Ucraino", "Polacco", "Tunisino"
]

# --- Memoria (Ping-Pong e Contesto) ---
if "lang_target" not in st.session_state:
    st.session_state.lang_target = "Francese" 
if "last_detected_lang" not in st.session_state:
    st.session_state.last_detected_lang = "Italiano" 
if "testo_tradotto" not in st.session_state:
    st.session_state.testo_tradotto = ""
if "storia_contesto" not in st.session_state:
    st.session_state.storia_contesto = ""
if "input_key_counter" not in st.session_state:
    st.session_state.input_key_counter = 0
if "modalita_selezionata" not in st.session_state:
    st.session_state.modalita_selezionata = None

def ping_pong_lingue():
    temp = st.session_state.lang_target
    st.session_state.lang_target = st.session_state.last_detected_lang
    st.session_state.last_detected_lang = temp
    st.session_state.testo_tradotto = ""

def nuova_chat():
    st.session_state.storia_contesto = ""
    st.session_state.testo_tradotto = ""
    st.session_state.input_key_counter += 1

# 4. Interfaccia Utente
st.markdown("**⚙️ Impostazioni Traduzione**")

# NUOVO LAYOUT: Colore dinamico per l'etichetta Modalità
colore_etichetta = "#ff4b4b" if st.session_state.modalita_selezionata is None else "inherit"

with st.container(border=True):
    col_lbl_mod, col_radio_mod = st.columns([1, 15])
    with col_lbl_mod:
        st.markdown(f"<div style='margin-top: 4px; color: {colore_etichetta};'><b>Modalità:</b></div>", unsafe_allow_html=True)
    with col_radio_mod:
        contesto_selezionato = st.radio(
            "Modalità:",
            ("🏢 B2B (Uffici, Broker e Clienti)", "👷‍♂️ FIELD (Autisti e Magazzino)"),
            horizontal=True,
            label_visibility="collapsed",
            index=None,
            key="modalita_selezionata"
        )

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# Expander Cronologia e Tasto Reset allineati a sinistra
with st.expander("📜 Cronologia & Contesto (Opzionale)", expanded=False):
    testo_contesto = st.text_area(
        "Incolla qui i messaggi precedenti o lascia che si popoli in automatico:", 
        value=st.session_state.storia_contesto, 
        height=120
    )
    st.session_state.storia_contesto = testo_contesto

st.button("🗑️ Svuota Contesto & 🔄 Inizia Nuova Chat", on_click=nuova_chat)

st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# Layout Colonne Lingue
col_lang_sx, col_btn_inv, col_lang_dx = st.columns([4, 1, 4])

with col_lang_sx:
    rilevamento_placeholder = st.empty()
    rilevamento_placeholder.text_input(
        "🌐 Rilevamento Automatico:", 
        value=st.session_state.last_detected_lang, 
        disabled=True
    )
    
with col_btn_inv:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("⇄ Inverti", on_click=ping_pong_lingue, use_container_width=True)
    
with col_lang_dx:
    opzioni_dinamiche = sorted(list(set(LINGUE_BASE + [st.session_state.lang_target, st.session_state.last_detected_lang])))
    st.selectbox("Traduci in:", opzioni_dinamiche, key="lang_target")

# Layout Testi
col_testo_sx, col_testo_dx = st.columns(2)

with col_testo_sx:
    testo_da_tradurre = st.text_area(
        "Testo Originale:", 
        height=250, 
        label_visibility="collapsed", 
        placeholder="Incolla qui il testo. La lingua verrà rilevata automaticamente...",
        key=f"input_{st.session_state.input_key_counter}"
    )
    btn_traduci = st.button("Traduci", type="primary", use_container_width=True)

with col_testo_dx:
    risultato_placeholder = st.empty()
    if st.session_state.testo_tradotto:
        risultato_placeholder.code(st.session_state.testo_tradotto, language=None, wrap_lines=True)

# 5. Logica di Rilevamento Istantaneo e Traduzione
if btn_traduci:
    # CONTROLLO BLOCCANTE SULLA MODALITA'
    if not contesto_selezionato:
        st.error("⚠️ Attenzione: Seleziona prima la Modalità (B2B o FIELD) nel riquadro in alto!")
    elif testo_da_tradurre.strip():
        
        # Assegnazione del prompt corretto basato sulla scelta
        prompt_attivo = PROMPT_B2B if "B2B" in contesto_selezionato else PROMPT_FIELD
        
        with st.spinner("Elaborazione e traduzione in corso... ⏳"):
            
            # A. RILEVAMENTO LINGUA ISTANTANEO
            try:
                codice_lingua = detect(testo_da_tradurre)
                lingua_rilevata = MAPPA_LINGUE.get(codice_lingua, f"Sconosciuta ({codice_lingua})")
            except LangDetectException:
                lingua_rilevata = "Non identificata"
                
            st.session_state.last_detected_lang = lingua_rilevata

            # B. PREPARAZIONE DEL COMANDO CON O SENZA CONTESTO
            lingua_destinazione = st.session_state.lang_target
            
            if st.session_state.storia_contesto.strip():
                comando_puro = f"""[STORICO DELLA CONVERSAZIONE - SOLO PER CONTESTO]:
{st.session_state.storia_contesto}

[ATTENZIONE - REGOLA TASSATIVA]:
Usa lo storico qui sopra ESCLUSIVAMENTE per capire l'argomento e il gergo. NON rispondere e NON continuare la conversazione. 
Fornisci SOLO ed ESCLUSIVAMENTE la traduzione finale pura, SENZA ripetere la frase "Traduci in...".

[TESTO DA TRADURRE ORA]:
Traduci in {lingua_destinazione}:
{testo_da_tradurre}"""
            else:
                comando_puro = f"Traduci in {lingua_destinazione}:\n\n{testo_da_tradurre}"

            prompt_completo = f"{prompt_attivo}\n\nInput:\n{comando_puro}"
            
            try:
                # C. CHIAMATA API E AGGIORNAMENTO
                response = model.generate_content(prompt_completo)
                st.session_state.testo_tradotto = response.text.strip()
                
                # Salviamo il nuovo scambio nella memoria del contesto
                nuovo_scambio = f"\n[Da {lingua_rilevata}]: {testo_da_tradurre}\n[In {lingua_destinazione}]: {st.session_state.testo_tradotto}\n---"
                st.session_state.storia_contesto += nuovo_scambio
                
                risultato_placeholder.code(st.session_state.testo_tradotto, language=None, wrap_lines=True)
                st.rerun() 
                
            except Exception as e:
                st.error(f"Errore con le API di Gemini: {e}")
    else:
        st.warning("Inserisci del testo da tradurre prima di cliccare su 'Traduci'.")
