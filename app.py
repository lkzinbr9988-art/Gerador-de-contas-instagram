import eventlet
eventlet.monkey_patch()

import os
import time
import random
import string
import secrets
import re
import datetime
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string
from flask_socketio import SocketIO
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.config['SECRET_KEY'] = 'insta_hacker_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

ARQUIVO_SAIDA = "contas_criadas.txt"

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insta Generator Console</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { background-color: #0d0d0d; color: #00ff00; font-family: 'Courier New', Courier, monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
        .header { text-align: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 10px; }
        .console { flex: 1; background-color: #000; border: 1px solid #00ff00; padding: 15px; overflow-y: auto; white-space: pre-wrap; box-shadow: 0 0 10px rgba(0, 255, 0, 0.2); font-size: 14px; }
        .controls { margin-top: 15px; text-align: center; }
        button { background-color: #000; color: #00ff00; border: 1px solid #00ff00; padding: 10px 20px; font-size: 16px; font-family: inherit; cursor: pointer; transition: 0.3s; }
        button:hover { background-color: #00ff00; color: #000; box-shadow: 0 0 15px #00ff00; }
        button:disabled { border-color: #333; color: #333; cursor: not-allowed; background-color: #000; box-shadow: none; }
        .status { font-size: 12px; color: #888; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header"><h2>[ INSTAGRAM ACCOUNT GENERATOR ]</h2></div>
    <div class="console" id="terminal">Aguardando conexão com o servidor...\n</div>
    <div class="controls">
        <button id="btnStart" onclick="startProcess()">INICIAR GERAÇÃO</button>
        <div class="status" id="status">Status: Offline</div>
    </div>
    <script>
        const socket = io();
        const terminal = document.getElementById('terminal');
        const btnStart = document.getElementById('btnStart');
        const statusText = document.getElementById('status');

        socket.on('connect', function() {
            terminal.innerHTML = "";
            appendLog("[SISTEMA] Conectado ao servidor em tempo real.");
            statusText.innerText = "Status: Aguardando comando...";
        });

        function appendLog(msg) {
            const time = new Date().toLocaleTimeString();
            terminal.innerHTML += `[${time}] ${msg}\n`;
            terminal.scrollTop = terminal.scrollHeight;
        }

        socket.on('console_log', function(msg) { appendLog(msg.data); });

        function startProcess() {
            btnStart.disabled = true;
            statusText.innerText = "Status: Processo em execução...";
            fetch('/start_gen')
                .then(response => response.json())
                .then(data => {
                    if (data.status === "iniciado") appendLog("[SISTEMA] Comando enviado ao backend...");
                })
                .catch(err => {
                    appendLog("[ERRO DE CONEXÃO] Falha ao comunicar com o servidor.");
                    btnStart.disabled = false;
                });
        }
        socket.on('finished', function() {
            btnStart.disabled = false;
            statusText.innerText = "Status: Processo finalizado.";
        });
    </script>
</body>
</html>
"""

def log_web(msg):
    print(msg)
    socketio.emit('console_log', {'data': msg})

class MailManager:
    def __init__(self):
        self.email = None
        self.token = None

    def criar_conta(self):
        try:
            r_dom = requests.get("https://api.mail.tm/domains", timeout=10)
            r_dom.raise_for_status()
            dominio = r_dom.json()["hydra:member"][0]["domain"]
            
            self.email = f"user_{secrets.token_hex(4)}@{dominio}"
            self.password = secrets.token_urlsafe(12)
            
            r_acc = requests.post("https://api.mail.tm/accounts", json={"address": self.email, "password": self.password}, timeout=10)
            r_acc.raise_for_status()
            
            r_token = requests.post("https://api.mail.tm/token", json={"address": self.email, "password": self.password}, timeout=10)
            self.token = r_token.json().get("token")
            return self.email
        except Exception as e:
            log_web(f"[ERRO TEMPMAIL] {e}")
            return None

    def obter_codigo_verificacao(self, timeout=120):
        headers = {"Authorization": f"Bearer {self.token}"}
        inicio = time.time()
        log_web("[SISTEMA] Aguardando e-mail de confirmação do Instagram...")
        
        while time.time() - inicio < timeout:
            try:
                r = requests.get("https://api.mail.tm/messages", headers=headers, timeout=10)
                msgs = r.json().get("hydra:member", [])
                
                for msg in msgs:
                    assunto = msg.get("subject", "").lower()
                    if "instagram" in assunto or "confirm" in assunto or "código" in assunto:
                        r_msg = requests.get(f"https://api.mail.tm/messages/{msg['id']}", headers=headers, timeout=10)
                        dados_msg = r_msg.json()
                        
                        texto = dados_msg.get("text", [""])[0] if dados_msg.get("text") else ""
                        html = dados_msg.get("html", [""])[0] if dados_msg.get("html") else ""
                        
                        soup = BeautifulSoup(html if html else texto, "html.parser")
                        texto_limpo = soup.get_text(separator=" ")
                            
                        match = re.search(r'\b(\d{6})\b', texto_limpo)
                        if match:
                            codigo = match.group(1)
                            if codigo not in ["2023", "2024", "2025", "2026"]:
                                return codigo
            except Exception:
                pass
            time.sleep(5)
        return None

def gerar_senha_forte():
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(14))

def gerar_data_nascimento():
    hoje = datetime.date.today()
    ano = hoje.year - random.randint(18, 45)
    mes = random.randint(1, 12)
    dia = random.randint(1, 28) if mes == 2 else random.randint(1, 30)
    return dia, mes, ano

def preencher_data_nascimento(driver):
    dia, mes, ano = gerar_data_nascimento()
    log_web(f"[INFO] Data gerada: {dia:02d}/{mes:02d}/{ano}")
    try:
        select_mes = driver.find_elements(By.XPATH, "//select[@title='Mês:' or contains(@aria-label, 'Month') or @name='month']")
        if select_mes: select_mes[0].send_keys(str(mes))
        select_dia = driver.find_elements(By.XPATH, "//select[@title='Dia:' or contains(@aria-label, 'Day') or @name='day']")
        if select_dia: select_dia[0].send_keys(str(dia))
        select_ano = driver.find_elements(By.XPATH, "//select[@title='Ano:' or contains(@aria-label, 'Year') or @name='year']")
        if select_ano: select_ano[0].send_keys(str(ano))
        btn_avancar = driver.find_elements(By.XPATH, "//button[contains(text(),'Avançar') or contains(text(), 'Next')]")
        if btn_avancar:
            btn_avancar[0].click()
            time.sleep(3)
    except Exception:
        pass

def processo_criacao():
    mail = MailManager()
    email = mail.criar_conta()
    if not email:
        log_web("[ERRO] Falha ao criar e-mail temporário.")
        socketio.emit('finished')
        return

    log_web(f"[*] Iniciando conta: {email}")
    senha_insta = gerar_senha_forte()
    usuario = f"u_{secrets.token_hex(4)}"
    
    options = uc.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-popup-blocking")
    
    driver = None
    try:
        log_web("[SISTEMA] Iniciando navegador (Undetected Chrome)...")
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 15)
        
        log_web("[SISTEMA] Acessando página de cadastro...")
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        
        wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='emailOrPhone' or @name='email']"))).send_keys(email)
        driver.find_element(By.XPATH, "//input[@name='fullName']").send_keys(f"User {secrets.token_hex(2)}")
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys(usuario)
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys(senha_insta)
        
        time.sleep(2)
        log_web("[SISTEMA] Enviando formulário...")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
        
        if "email" in driver.page_source.lower() and "inválido" in driver.page_source.lower():
            log_web("[ERRO] Domínio bloqueado pelo Instagram.")
            socketio.emit('finished')
            return

        preencher_data_nascimento(driver)

        log_web("[SISTEMA] Verificando tela de código...")
        try:
            input_codigo = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='confirmationCode' or @name='email_confirmation_code']")))
        except Exception:
            log_web("[ERRO] O Instagram bloqueou o IP, exigiu telefone ou CAPTCHA.")
            socketio.emit('finished')
            return

        codigo = mail.obter_codigo_verificacao()
        
        if codigo:
            log_web(f"[+] Código recebido: {codigo}. Inserindo...")
            input_codigo.send_keys(codigo)
            driver.find_element(By.XPATH, "//button[@type='submit' or contains(text(), 'Avançar')]").click()
            time.sleep(5)
        else:
            log_web("[ERRO] Código não recebido no tempo limite.")
            socketio.emit('finished')
            return

        if "challenge" in driver.current_url:
            log_web("[ERRO] Bloqueado por Checkpoint de segurança.")
            socketio.emit('finished')
            return
            
        if not driver.find_elements(By.XPATH, "//a[contains(@href, '/direct/inbox/')]") and "instagram.com" not in driver.current_url:
             log_web("[ERRO] Sessão não estabelecida.")
             socketio.emit('finished')
             return

        log_web(f"[+++] SUCESSO! Conta: {usuario} | {email} | {senha_insta}")
        with open(ARQUIVO_SAIDA, "a", encoding="utf-8") as f:
            f.write(f"Email: {email} | Senha: {senha_insta} | User: {usuario}\n")
            
    except Exception as e:
        log_web(f"[ERRO CRÍTICO] {e}")
    finally:
        if driver:
            driver.quit()
            log_web("[SISTEMA] Navegador fechado. Processo finalizado.")
            socketio.emit('finished')

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/start_gen')
def start_gen():
    socketio.start_background_task(processo_criacao)
    return {"status": "iniciado"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Servidor rodando na porta {port}")
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
