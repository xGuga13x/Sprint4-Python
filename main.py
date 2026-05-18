# Ponto de entrada do sistema Turma do Bem
#
# Gustavo Rodrigues Siciliano — RM568419
# Gustavo de Jesus Silva      — RM567926
# Samuel Keniti Kina de Lima  — RM567614
#
# Executar: python main.py

from config import VERDE, LARANJA, AZUL, AMARELO, RESET
from ui import limpar, titulo, pausar, menu_opcao
from db import conectar
from pacientes import menu_pacientes
from consultas import menu_consultas, menu_relatorios
from apis import verificar_api_ia, prever_falta, prever_arrecadacao


def cabecalho():
    limpar()
    print(f"""
{VERDE}╔══════════════════════════════════════════════════════╗
║       DE NOVO NAO! — Sistema de Gestao              ║
║       Turma do Bem x FIAP — Sprint 4                ║
╚══════════════════════════════════════════════════════╝{RESET}

{AZUL}Integrantes:{RESET}
  Gustavo Rodrigues Siciliano — RM568419
  Gustavo de Jesus Silva      — RM567926
  Samuel Keniti Kina de Lima  — RM567614
""")


def menu_ia(conn):
    while True:
        limpar()
        titulo('INTELIGENCIA ARTIFICIAL', AMARELO)
        op = menu_opcao({
            '1': 'Verificar status da API de IA',
            '2': 'Prever risco de falta',
            '3': 'Prever arrecadacao de campanha',
            '0': 'Voltar',
        }, 'MENU — IA', AMARELO)
        if op == '0':
            break
        elif op == '1':
            verificar_api_ia()
            pausar()
        elif op == '2':
            prever_falta(conn)
            pausar()
        elif op == '3':
            prever_arrecadacao()
            pausar()
        else:
            print(f'{LARANJA}Opcao invalida.{RESET}')
            pausar()


def main():
    cabecalho()
    print(f'{AMARELO}Conectando ao banco Oracle...{RESET}')
    conn = conectar()
    if not conn:
        print(f'\n{LARANJA}Falha na conexao. Verifique a rede FIAP ou VPN.{RESET}')
        input('\nENTER para sair...')
        return
    print(f'{VERDE}Conexao estabelecida!{RESET}')
    pausar()
    while True:
        limpar()
        titulo('MENU PRINCIPAL', VERDE)
        op = menu_opcao({
            '1': 'Pacientes',
            '2': 'Consultas',
            '3': 'Relatorios',
            '4': 'Inteligencia Artificial',
            '0': 'Sair',
        }, 'O QUE DESEJA FAZER?')
        if op == '0':
            if conn:
                conn.close()
            limpar()
            print(f'\n{VERDE}Sistema encerrado.{RESET}\n')
            break
        elif op == '1':
            menu_pacientes(conn)
        elif op == '2':
            menu_consultas(conn)
        elif op == '3':
            menu_relatorios(conn)
        elif op == '4':
            menu_ia(conn)
        else:
            print(f'{LARANJA}Opcao invalida.{RESET}')
            pausar()


if __name__ == '__main__':
    main()
