# Utilitários de exibição, menus e validações de entrada

import os
import re
import datetime
from config import VERDE, LARANJA, AZUL, AMARELO, RESET, NEGRITO


def limpar():
    os.system('cls' if os.name == 'nt' else 'clear')

def linha(cor=VERDE):
    print(f'{cor}{"=" * 58}{RESET}')

def titulo(texto, cor=VERDE):
    linha(cor)
    print(f'{cor}{NEGRITO}  {texto}{RESET}')
    linha(cor)

def pausar():
    input(f'\n{AZUL}Pressione ENTER para continuar...{RESET}')

def confirmar(msg):
    return input(f'{LARANJA}{msg} (s/n): {RESET}').strip().lower() == 's'

def menu_opcao(opcoes, titulo_menu, cor=VERDE):
    print(f'\n{cor}{NEGRITO}{titulo_menu}{RESET}')
    linha(cor)
    for k, v in opcoes.items():
        print(f'  {LARANJA}{k}{RESET} - {v}')
    linha(cor)
    return input(f'{AZUL}Opcao: {RESET}').strip()

def validar_cpf(cpf):
    return len(re.sub(r'\D', '', cpf)) == 11

def formatar_cpf(cpf):
    c = re.sub(r'\D', '', cpf)
    return f'{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}'

def validar_telefone(tel):
    return 8 <= len(re.sub(r'\D', '', tel)) <= 11

def validar_data(data):
    try:
        datetime.datetime.strptime(data, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def validar_horario(h):
    return bool(re.match(r'^([01]\d|2[0-3]):[0-5]\d$', h))

def validar_cep(cep):
    return len(re.sub(r'\D', '', cep)) == 8

def input_validado(prompt, fn_valida, msg_erro, opcional=False):
    while True:
        v = input(f'{AZUL}{prompt}{RESET}').strip()
        if opcional and not v:
            return v
        if fn_valida(v):
            return v
        print(f'{LARANJA}{msg_erro}{RESET}')

def input_opcao(prompt, validas):
    while True:
        v = input(f'{AZUL}{prompt}{RESET}').strip().upper()
        if v in validas:
            return v
        print(f'{LARANJA}Opcao invalida. Escolha: {", ".join(validas)}{RESET}')
