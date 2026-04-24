import streamlit as st
import google.generativeai as genai

# 1. Configurazione della pagina
st.set_page_config(page_title="Traduttore Logistico AI", page_icon="🚛", layout="wide")

# Iniezione CSS per ridurre lo spazio vuoto in alto
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("## Traduttore AI settore Logistica 🚛")
st.markdown("Seleziona il contesto. Il sistema rileva in automatico la lingua di partenza.")

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

# --- NUOVA GESTIONE DELLA MEMORIA (Ping-Pong) ---
if "lang_target" not in st.session_state:
    st.session_state.lang_target = "Tedesco" 
if "last_detected_lang" not in st.session_state:
    st.session_state.last_detected_lang = "Italiano" 
if "testo_tradotto" not in st.session_state:
    st.session_state.testo_tradotto = ""

def ping_pong_lingue():
    # Inverte la destinazione con l'ultima lingua rilevata dal testo
    temp = st.session_state.lang_target
    st.session_state.lang_target = st.session_state.last_detected_lang
    st.session_state.last_detected_lang = temp
    # Svuota il risultato precedente
    st.session_state.testo_tradotto = ""

# 4. Interfaccia Utente
st.markdown("**⚙️ Impostazioni Traduzione**")

contesto_selezionato = st.radio(
    "Modalità:",
    ("B2B (Uffici, Broker e Clienti)", "FIELD (Autisti e Magazzino)"),
    horizontal=True
)

st.markdown("<hr style='margin-top: 10px; margin-bottom: 20px;'>", unsafe_allow_html=True)
prompt_attivo = PROMPT_B2B if "B2B" in contesto_selezionato else PROMPT_FIELD

# Layout Colonne Lingue
col_lang_sx, col_btn_inv, col_lang_dx = st.columns([4, 1, 4])

with col_lang_sx:
    st.markdown("<div style='margin-top: 5px; color: #aaaaaa;'>🌐 <b>Rilevamento Automatico</b></div>", unsafe_allow_html=True)
    st.info(f"Ultima lingua rilevata: **{st.session_state.last_detected_lang}**")
    
with col_btn_inv:
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    st.button("⇄ Inverti", on_click=ping_pong_lingue, use_container_width=True)
    
with col_lang_dx:
    opzioni_dinamiche = sorted(list(set(LINGUE_BASE + [st.session_state.lang_target, st.session_state.last_detected_lang])))
    st.selectbox("Traduci in:", opzioni_dinamiche, key="lang_target")

# Layout Testi
col_testo_sx, col_testo_dx = st.columns(2)

with col_testo_sx:
    testo_da_tradurre = st.text_area("Testo Originale:", height=250, label_visibility="collapsed", placeholder="Incolla qui il testo. La lingua verrà rilevata automaticamente...")
    btn_traduci = st.button("Traduci", type="primary", use_container_width=True)

with col_testo_dx:
    if st.session_state.testo_tradotto:
        st.code(st.session_state.testo_tradotto, language=None, wrap_lines=True)

# 5. Logica di Rilevamento e Traduzione
if btn_traduci:
    if testo_da_tradurre.strip():
        with st.spinner("Rilevamento e traduzione (Flash Lite)..."):
            lingua_destinazione = st.session_state.lang_target
            
            # Formatta l'output per separare il rilevamento dalla traduzione
            comando_invisibile = f"""Identifica la lingua del testo seguente e traducilo in {lingua_destinazione}.
FORMATO DI OUTPUT OBBLIGATORIO:
LINGUA: [Nome lingua rilevata in Italiano]
---
[Solo la traduzione pura, senza commenti o introduzioni]

Testo originale da tradurre:
{testo_da_tradurre}"""
            
            prompt_completo = f"{prompt_attivo}\n\nInput:\n{comando_invisibile}"
            
            try:
                response = model.generate_content(prompt_completo)
                risposta_grezza = response.text
                
                # Parsing
                if "---" in risposta_grezza:
                    parti = risposta_grezza.split("---", 1)
                    lingua_rilevata = parti[0].replace("LINGUA:", "").strip()
                    traduzione = parti[1].strip()
                else:
                    lingua_rilevata = "Sconosciuta"
                    traduzione = risposta_grezza.strip()
                
                # Aggiorna la memoria e ricarica
                st.session_state.last_detected_lang = lingua_rilevata
                st.session_state.testo_tradotto = traduzione
                st.rerun()
                
            except Exception as e:
                st.error(f"Si è verificato un errore con le API di Gemini: {e}")
    else:
        st.warning("Inserisci del testo da tradurre prima di cliccare su 'Traduci'.")
