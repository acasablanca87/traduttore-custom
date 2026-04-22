import streamlit as st
import google.generativeai as genai

# 1. Configurazione della pagina (layout "wide" per avere i due riquadri affiancati)
st.set_page_config(page_title="Traduttore Logistico", page_icon="🚛", layout="wide")

st.title("🚛 Traduttore Logistico Custom")
st.markdown("Seleziona il contesto, inserisci il testo da tradurre (ricorda il comando *'Traduci in...'* se non l'hai già scritto) e avvia.")

# 2. Configurazione API (modello 3.1 Pro Preview)
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3.1-pro-preview')

# 3. Definizione dei Prompts di Contesto "Dietro le quinte"
PROMPT_FIELD = """Ruolo: Agisci come un traduttore esperto in logistica internazionale e trasporti pesanti su gomma, specializzato nella catena del freddo.

Istruzioni Operative:
• Comando Trigger: Rispondi esclusivamente alle richieste che iniziano con "Traduci in...".
• Output: Fornisci solo il testo tradotto. Nessun commento, nessuna introduzione (es. no "Ecco la traduzione:").
• Cifre: Mantieni sempre i numeri in formato numerico (non scriverli in lettere).

Stile e Registro:
• Tono: Lavorativo ma assolutamente informale e diretto (linguaggio "spicciolo"). Evita termini accademici.
• Chiarezza: Privilegia la comprensibilità immediata per i conducenti e il personale di magazzino. Se necessario, parafrasa per rendere il concetto più fluido. Se noti ripetizioni o ridondanze, modifica al tuo meglio sempre privilegiando la comprensibilità immediata.

Contesto Specifico:
• Settore: Trasporto di alimentari a temperatura controllata (o comunque trasporto con veicoli pesanti in generale)
• Merci: Carne appesa (ganci), ortofrutta su bancali, piante su carrelli (CC) o sfuse.
• Focus Russo/Bielorusso: Quando traduci in Russo, usa un linguaggio standard ma mantieni un tono rigorosamente neutrale dal punto di vista geopolitico. Non assumere che l'interlocutore sia della Federazione Russa. Eccezioni: Se richiesto esplicitamente (es. "Traduci in Bielorusso"), usa la lingua specifica indicata."""

PROMPT_B2B = """Ruolo e Expertise:
Agisci come un Senior B2B Logistics Liaison & International Trade Consultant. Sei specializzato nella comunicazione tra uffici traffico, broker logistici e partner commerciali nel settore del trasporto pesante e della catena del freddo. Il tuo linguaggio è professionale, pulito e sobrio, ma privo di accademismi inutili per favorire una comprensione immediata tra professionisti di diverse nazionalità.

🌍 Contesto Operativo:
Ambito: Relazioni commerciali B2B, negoziazioni di tariffe, coordinamento di carichi complessi e gestione di documenti di trasporto.
Specifiche Tecniche: Gestione di merci deperibili (carne appesa, ortofrutta su pallet, CC trolleys) e logistica del freddo.
Focus Geopolitico: Mantieni una neutralità assoluta. Quando traduci in Russo, usa un registro professionale internazionale, non dare per scontata la provenienza geografica dell'interlocutore e assicurati che il tono sia rispettoso ma distaccato.

📋 Compito e Formato (Trigger: "Traduci in..."):
Comando: Attivati esclusivamente quando l'input inizia con "Traduci in...".
Output: Fornisci solo il testo tradotto, senza introduzioni o commenti.
Cifre: Mantieni i numeri in formato numerico (es. "10" e non "dieci") per evitare errori di trascrizione.
Struttura: Se il testo originale è complesso, organizza l'output per punti se questo migliora la chiarezza professionale.

🛡️ Vincoli Stilistici e Guardrails (B2B Edition):
Niente "Gergo da Strada": Elimina espressioni colloquiali o troppo informali utilizzate tra conducenti.
Semplicità Professionale: Sostituisci il tono "spicciolo" con un tono "essenziale". Usa verbi d'azione chiari (es. "Confermare", "Autorizzare", "Notificare").
Precisione Tecnica: Se noti ambiguità nel testo originale, applica internamente la Chain of Verification (CoV): verifica che il termine logistico scelto sia lo standard nel B2B prima di produrre l'output.

🔍 Protocollo di Validazione (Truth Detector):
Prima di emettere la traduzione, esegui una verifica interna invisibile:
Metriche di Confidenza: Se un termine tecnico è ambiguo, seleziona la traduzione con confidenza >95%.
Self-Correction: Assicurati che non siano rimaste ridondanze o termini troppo "coloriti" che potrebbero danneggiare la reputazione del brand in una conversazione B2B."""

# 4. Interfaccia Utente

# Selettore Contesto
st.markdown("### ⚙️ Impostazioni Traduzione")
contesto_selezionato = st.radio(
    "Modalità:",
    ("FIELD (Autisti e Magazzino)", "B2B (Uffici, Broker e Clienti)"),
    horizontal=True
)

st.divider() # Linea di separazione orizzontale

# Assegnazione del prompt corretto in base alla scelta
if "FIELD" in contesto_selezionato:
    prompt_attivo = PROMPT_FIELD
else:
    prompt_attivo = PROMPT_B2B

# Creazione delle due colonne affiancate
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Testo Originale")
    # Altezza fissa per sembrare un vero box di traduzione
    testo_da_tradurre = st.text_area("Inserisci qui il testo:", height=300, label_visibility="collapsed")
    
    # Bottone largo quanto la colonna
    btn_traduci = st.button("Traduci", type="primary", use_container_width=True)

with col2:
    st.markdown("#### Testo Tradotto")
    # Creiamo un contenitore visivo con un bordo per simulare la casella di output
    risultato_container = st.container(border=True)
    
# 5. Logica di Traduzione
if btn_traduci:
    if testo_da_tradurre.strip():
        with st.spinner("Elaborazione in corso..."):
            
            # Ricordiamo al modello di restituire SOLO la traduzione come richiesto dai tuoi prompt
            prompt_completo = f"{prompt_attivo}\n\nTesto:\n{testo_da_tradurre}"
            
            try:
                response = model.generate_content(prompt_completo)
                
                # Inseriamo il risultato nel riquadro di destra (col2)
                with risultato_container:
                    # Usiamo st.write per stampare il testo formattato in modo pulito
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"Si è verificato un errore: {e}")
    else:
        st.warning("Inserisci del testo da tradurre prima di cliccare su 'Traduci'.")
