# Configurações gerais do sistema
# Credenciais lidas de variáveis de ambiente em produção (Render).
# Para rodar local: crie um arquivo .env ou exporte as vars manualmente.

import os

# ─── Banco Oracle ─────────────────────────────────────────────────────────────
DB_CONFIG = {
    'user':     os.getenv('DB_USER',     'rm568419'),
    'password': os.getenv('DB_PASSWORD', ''),        # nunca commite a senha real
    'host':     os.getenv('DB_HOST',     'oracle.fiap.com.br'),
    'port':     int(os.getenv('DB_PORT', '1521')),
    'sid':      os.getenv('DB_SID',      'orcl'),
}

# ─── URLs externas ────────────────────────────────────────────────────────────
API_IA  = os.getenv('API_IA',  'https://turma-do-bem-ia.onrender.com')
API_CEP = os.getenv('API_CEP', 'https://viacep.com.br/ws')

# ─── Timeouts ────────────────────────────────────────────────────────────────
TIMEOUT_IA  = int(os.getenv('TIMEOUT_IA',  '60'))
TIMEOUT_CEP = int(os.getenv('TIMEOUT_CEP', '5'))

# ─── Cores ANSI (terminal) ────────────────────────────────────────────────────
VERDE   = '\033[38;5;34m'
LARANJA = '\033[38;5;208m'
AZUL    = '\033[38;5;75m'
ROXO    = '\033[38;5;135m'
AMARELO = '\033[38;5;220m'
RESET   = '\033[m'
NEGRITO = '\033[1m'
