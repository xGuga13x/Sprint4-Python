# Conexão e utilitários do banco Oracle

import oracledb
from config import DB_CONFIG, LARANJA, RESET


def conectar():
    try:
        return oracledb.connect(**DB_CONFIG)
    except Exception as e:
        print(f'\n{LARANJA}Erro ao conectar: {e}{RESET}')
        return None


def proximo_id(conn, tabela, coluna):
    try:
        cur = conn.cursor()
        cur.execute(f'SELECT NVL(MAX({coluna}), 0) + 1 FROM {tabela}')
        return cur.fetchone()[0]
    except Exception:
        return 1