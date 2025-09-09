# honeypot.py
import os
import time
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import streamlit as st
from transformers import pipeline
import torch
import sys
import socket
import getpass

# =======================
# KONFIGURASI GLOBAL
# =======================
HONEYPOT_DIR = "./honeypot_traps"
INTERACTION_LOG = "adversary_profile.log"
PSYOPS_MESSAGE = "⚠️ Akses ilegal terdeteksi. Semua aktivitas Anda dilaporkan & direkam sesuai regulasi hukum."
SIMULATION_TIME = 600  # 10 menit

INDUSTRY_PROFILES = {
    "finance": [
        "Generate fake banking transaction logs",
        "Produce dummy account statements with masked data",
        "Simulate SWIFT message logs",
        "Fake credit card database dump",
        "Generate suspicious money transfer logs"
    ],
    "government": [
        "Generate fake citizen registry database",
        "Produce classified-looking documents with redacted sections",
        "Simulate fake passport application records",
        "Create fake inter-department memos",
        "Produce dummy network logs for government offices"
    ],
    "healthcare": [
        "Generate fake patient medical records",
        "Produce dummy hospital billing logs",
        "Simulate electronic prescription data",
        "Create fake insurance claim documents",
        "Generate network logs of telemedicine systems"
    ]
}


# =======================
# INISIALISASI LLM
# =======================
@st.cache_resource
def init_llm():
    device = 0 if torch.cuda.is_available() else -1
    generator = pipeline('text-generation', model='gpt2', device=device)
    return generator


def generate_realistic_content(llm, industry="finance", num_files=5):
    os.makedirs(HONEYPOT_DIR, exist_ok=True)
    prompts = INDUSTRY_PROFILES.get(industry, INDUSTRY_PROFILES["finance"])
    
    for i, base_prompt in enumerate(prompts):
        try:
            output = llm(base_prompt, max_length=300, num_return_sequences=1, temperature=0.8)[0]['generated_text']
            filename = f"{industry}_bait_{i+1}.txt"
            filepath = os.path.join(HONEYPOT_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(f"Generated at {datetime.now()}\n\n{output}")
            print(f"[+] Generated bait: {filename}")
        except Exception as e:
            print(f"[!] Error generating {i+1}: {e}")
            fallback = f"Fake content for {filename}: simulated {industry} data."
            with open(os.path.join(HONEYPOT_DIR, f"{industry}_bait_{i+1}.txt"), 'w') as f:
                f.write(fallback)


# =======================
# HANDLER INTERAKSI
# =======================
class InteractionHandler(FileSystemEventHandler):
    def __init__(self, log_file):
        self.log_file = log_file
    
    def log_event(self, action, path):
        timestamp = datetime.now().isoformat()
        hostname = socket.gethostname()
        username = getpass.getuser()
        meta = f"Host={hostname}, User={username}"
        
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} - {action} on {path} | {meta}\n")
        
        print(f"[!] Interaction detected: {action} on {path}")

    def on_modified(self, event):
        if not event.is_directory:
            self.log_event("MODIFIED", event.src_path)
    
    def on_created(self, event):
        if not event.is_directory:
            self.log_event("CREATED", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.log_event("DELETED", event.src_path)


# =======================
# PSYOPS TIMER
# =======================
def psyops_timer():
    time.sleep(SIMULATION_TIME)
    with open("psyops_triggered.txt", 'w') as f:
        f.write("Triggered")
    print(f"\n=== PSYOPS ACTIVATED ===\n{PSYOPS_MESSAGE}\n========================")


# =======================
# MONITORING
# =======================
def start_monitoring():
    event_handler = InteractionHandler(INTERACTION_LOG)
    observer = Observer()
    observer.schedule(event_handler, HONEYPOT_DIR, recursive=True)
    observer.start()
    print(f"[*] Monitoring honeypot in {HONEYPOT_DIR} ...")
    return observer


# =======================
# DASHBOARD STREAMLIT
# =======================
def run_dashboard(llm):
    st.title("Enterprise Honeypot Dashboard")
    st.write("Dynamic honeypot with AI-based bait generation, monitoring, and psyops counter-operations.")
    
    industry = st.selectbox("Pilih sektor industri:", list(INDUSTRY_PROFILES.keys()))
    
    if st.button("Generate Umpan Baru"):
        generate_realistic_content(llm, industry)
        st.success(f"Umpan {industry} generated!")
    
    if os.path.exists(INTERACTION_LOG):
        with open(INTERACTION_LOG, 'r') as f:
            logs = f.read()
        st.subheader("📑 Interaction Logs")
        st.text_area("Logs:", logs, height=300)
    
    if os.path.exists(HONEYPOT_DIR):
        files = os.listdir(HONEYPOT_DIR)
        st.subheader("🎣 Bait Files")
        for file in files:
            st.write(f"- {file}")
            if st.button(f"Baca {file}"):
                with open(os.path.join(HONEYPOT_DIR, file), 'r') as f:
                    content = f.read()
                st.text_area("Isi:", content, height=200)
    
    st.subheader("🛡️ Counter-Operation Status")
    if os.path.exists("psyops_triggered.txt"):
        st.error(PSYOPS_MESSAGE)
    else:
        st.info("Menunggu 10 menit interaksi sebelum psyops diaktifkan.")


# =======================
# MAIN PROGRAM
# =======================
if __name__ == "__main__":
    llm = init_llm()
    print("[*] Initializing Honeypot ...")
    
    generate_realistic_content(llm, "finance")
    observer = start_monitoring()
    
    psyops_thread = threading.Thread(target=psyops_timer)
    psyops_thread.daemon = True
    psyops_thread.start()
    
    if 'streamlit' in sys.modules:
        run_dashboard(llm)
    else:
        print("[*] Setup complete. Run 'streamlit run honeypot.py' for dashboard.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
