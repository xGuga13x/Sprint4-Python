# CRUD de Consultas e Relatórios com validações e exportação JSON

import json
import os
import datetime
from config import VERDE, LARANJA, AZUL, ROXO, RESET, NEGRITO
from ui import (
    limpar, titulo, pausar, confirmar, menu_opcao,
    validar_data, validar_horario, input_validado, input_opcao, linha,
)
from db import proximo_id

STATUS_MAP = {'1': 'AGENDADA', '2': 'REALIZADA', '3': 'CANCELADA', '4': 'FALTA'}


def _consulta_existe(cur, id_c):
    cur.execute('SELECT 1 FROM tdb_Consulta WHERE id_consulta = :id', id=id_c)
    return cur.fetchone() is not None


def _data_futura(data_str):
    try:
        return datetime.datetime.strptime(data_str, '%d/%m/%Y').date() >= datetime.date.today()
    except ValueError:
        return False


def listar_consultas(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id_consulta, pe_pac.nome, pe_den.nome,
                   TO_CHAR(c.data_consulta, 'DD/MM/YYYY'),
                   c.horario, c.turno, c.status, c.tipo
            FROM tdb_Consulta c
            JOIN tdb_Paciente pa ON pa.id_paciente = c.id_paciente
            JOIN tdb_Pessoa pe_pac ON pe_pac.cpf = pa.cpf
            JOIN tdb_Dentista den ON den.cro = c.cro_dentista AND den.cpf = c.cpf_dentista
            JOIN tdb_Pessoa pe_den ON pe_den.cpf = den.cpf
            ORDER BY c.data_consulta DESC
        """)
        rows = cur.fetchall()
        if not rows:
            print(f'\n{LARANJA}Nenhuma consulta encontrada.{RESET}')
            return
        print(f'\n{AZUL}{NEGRITO}{"ID":<5} {"Paciente":<25} {"Dentista":<22} {"Data":<12} {"Status"}{RESET}')
        linha(AZUL)
        for r in rows:
            print(f'{r[0]:<5} {r[1][:24]:<25} {r[2][:21]:<22} {r[3]:<12} {r[6]}')
    except Exception as e:
        print(f'{LARANJA}Erro ao listar: {e}{RESET}')


def inserir_consulta(conn):
    titulo('AGENDAR CONSULTA', AZUL)
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT pa.id_paciente, pe.nome, pa.cpf
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            ORDER BY pe.nome
        """)
        pacientes = cur.fetchall()
        if not pacientes:
            print(f'{LARANJA}Nenhum paciente cadastrado.{RESET}')
            return

        print(f'\n{VERDE}Pacientes:{RESET}')
        ids_validos = [p[0] for p in pacientes]
        for p in pacientes:
            print(f'  {LARANJA}{p[0]}{RESET} - {p[1]}')

        while True:
            try:
                id_pac = int(input(f'\n{AZUL}ID do paciente: {RESET}').strip())
                if id_pac not in ids_validos:
                    print(f'{LARANJA}ID nao encontrado na lista.{RESET}')
                    continue
                break
            except ValueError:
                print(f'{LARANJA}Informe apenas numeros.{RESET}')

        pac = next(p for p in pacientes if p[0] == id_pac)

        cur.execute("""
            SELECT den.cro, pe.nome, den.cpf, den.especialidade
            FROM tdb_Dentista den
            JOIN tdb_Pessoa pe ON pe.cpf = den.cpf
            ORDER BY pe.nome
        """)
        dentistas = cur.fetchall()
        if not dentistas:
            print(f'{LARANJA}Nenhum dentista cadastrado.{RESET}')
            return

        print(f'\n{VERDE}Dentistas:{RESET}')
        cros_validos = [d[0] for d in dentistas]
        for d in dentistas:
            print(f'  {LARANJA}{d[0]}{RESET} - {d[1]} ({d[3] or "Clinico Geral"})')

        while True:
            cro = input(f'\n{AZUL}CRO do dentista: {RESET}').strip().upper()
            if not cro:
                print(f'{LARANJA}CRO obrigatorio.{RESET}')
            elif cro not in cros_validos:
                print(f'{LARANJA}CRO nao encontrado na lista.{RESET}')
            else:
                break
        den = next(d for d in dentistas if d[0] == cro)

        while True:
            data_c = input_validado('Data (DD/MM/AAAA): ', validar_data, 'Data invalida. Use DD/MM/AAAA.')
            if not _data_futura(data_c):
                print(f'{LARANJA}Informe uma data futura ou hoje.{RESET}')
                continue
            break

        horario = input_validado('Horario (HH:MM): ', validar_horario, 'Horario invalido. Use HH:MM.')

        cur.execute("""
            SELECT COUNT(*) FROM tdb_Consulta
            WHERE cro_dentista = :cro AND cpf_dentista = :cpf
              AND data_consulta = TO_DATE(:data, 'DD/MM/YYYY')
              AND horario = :hor AND status NOT IN ('CANCELADA')
        """, cro=cro, cpf=den[2], data=data_c, hor=horario)
        if cur.fetchone()[0] > 0:
            print(f'{LARANJA}Dentista ja tem consulta neste horario.{RESET}')
            return

        print(f'{LARANJA}Turno:  1-MANHA  2-TARDE  3-NOITE{RESET}')
        turno = {'1': 'MANHA', '2': 'TARDE', '3': 'NOITE'}[input_opcao('Turno: ', ['1', '2', '3'])]
        tipo = input(f'{AZUL}Tipo (ex: Limpeza, Avaliacao): {RESET}').strip() or None

        while True:
            try:
                dist = float(input(f'{AZUL}Distancia percorrida km (0 se nao souber): {RESET}').strip() or '0')
                if dist < 0:
                    print(f'{LARANJA}Distancia nao pode ser negativa.{RESET}')
                    continue
                break
            except ValueError:
                print(f'{LARANJA}Valor invalido.{RESET}')

        obs = input(f'{AZUL}Observacoes (opcional): {RESET}').strip() or None

        print(f'\n{AZUL}--- Resumo ---{RESET}')
        print(f'  Paciente: {pac[1]}')
        print(f'  Dentista: {den[1]}')
        print(f'  Data: {data_c} {horario} ({turno})')
        print(f'  Tipo: {tipo or "-"}')

        if not confirmar('Confirmar agendamento?'):
            print(f'{LARANJA}Cancelado.{RESET}')
            return

        id_c = proximo_id(conn, 'tdb_Consulta', 'id_consulta')
        cur.execute("""
            INSERT INTO tdb_Consulta
                (id_consulta, id_paciente, cpf_paciente,
                 cro_dentista, cpf_dentista, data_consulta,
                 horario, turno, status, tipo, distancia_km, observacoes)
            VALUES (:id, :id_pac, :cpf_pac, :cro, :cpf_den,
                    TO_DATE(:data, 'DD/MM/YYYY'),
                    :hor, :turno, 'AGENDADA', :tipo, :dist, :obs)
        """, id=id_c, id_pac=id_pac, cpf_pac=pac[2],
             cro=cro, cpf_den=den[2], data=data_c,
             hor=horario, turno=turno, tipo=tipo, dist=dist, obs=obs)
        conn.commit()
        print(f'\n{VERDE}Consulta agendada! ID: {id_c}{RESET}')

    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao agendar: {e}{RESET}')


def alterar_status_consulta(conn):
    titulo('ALTERAR STATUS', AZUL)
    listar_consultas(conn)

    while True:
        try:
            id_c = int(input(f'\n{AZUL}ID da consulta (0 para cancelar): {RESET}').strip())
            break
        except ValueError:
            print(f'{LARANJA}ID invalido.{RESET}')
    if id_c == 0:
        return

    try:
        cur = conn.cursor()
        if not _consulta_existe(cur, id_c):
            print(f'{LARANJA}Consulta ID {id_c} nao encontrada.{RESET}')
            return

        cur.execute('SELECT status FROM tdb_Consulta WHERE id_consulta = :id', id=id_c)
        status_atual = cur.fetchone()[0]

        if status_atual == 'CANCELADA':
            print(f'{LARANJA}Consulta ja cancelada e nao pode ser alterada.{RESET}')
            return

        print(f'\n{LARANJA}Status atual: {status_atual}{RESET}')
        print('  1-AGENDADA  2-REALIZADA  3-CANCELADA  4-FALTA')
        novo = STATUS_MAP[input_opcao('Novo status: ', ['1', '2', '3', '4'])]

        if novo == status_atual:
            print(f'{LARANJA}Status ja e {status_atual}. Nenhuma alteracao feita.{RESET}')
            return

        obs = input(f'{AZUL}Observacao (opcional): {RESET}').strip() or None

        cur.execute("""
            UPDATE tdb_Consulta SET status = :s, observacoes = NVL(:obs, observacoes)
            WHERE id_consulta = :id
        """, s=novo, obs=obs, id=id_c)
        conn.commit()
        print(f'\n{VERDE}Status atualizado para {novo}.{RESET}')

    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao alterar: {e}{RESET}')


def excluir_consulta(conn):
    titulo('EXCLUIR CONSULTA', LARANJA)
    listar_consultas(conn)

    while True:
        try:
            id_c = int(input(f'\n{AZUL}ID da consulta (0 para cancelar): {RESET}').strip())
            break
        except ValueError:
            print(f'{LARANJA}ID invalido.{RESET}')
    if id_c == 0:
        return

    try:
        cur = conn.cursor()
        if not _consulta_existe(cur, id_c):
            print(f'{LARANJA}Consulta ID {id_c} nao encontrada.{RESET}')
            return

        cur.execute('SELECT status FROM tdb_Consulta WHERE id_consulta = :id', id=id_c)
        if cur.fetchone()[0] == 'REALIZADA':
            print(f'{LARANJA}Consultas realizadas nao podem ser excluidas.{RESET}')
            return

        if not confirmar('Confirmar exclusao?'):
            print(f'{LARANJA}Cancelado.{RESET}')
            return

        cur.execute('DELETE FROM tdb_Consulta WHERE id_consulta = :id', id=id_c)
        conn.commit()
        print(f'\n{VERDE}Consulta excluida.{RESET}')

    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao excluir: {e}{RESET}')


def menu_consultas(conn):
    while True:
        limpar()
        titulo('GESTAO DE CONSULTAS', AZUL)
        op = menu_opcao({
            '1': 'Listar todas',
            '2': 'Agendar nova consulta',
            '3': 'Alterar status',
            '4': 'Excluir consulta',
            '0': 'Voltar',
        }, 'MENU — CONSULTAS', AZUL)
        if op == '0':
            break
        elif op == '1':
            listar_consultas(conn)
            pausar()
        elif op == '2':
            inserir_consulta(conn)
            pausar()
        elif op == '3':
            alterar_status_consulta(conn)
            pausar()
        elif op == '4':
            excluir_consulta(conn)
            pausar()
        else:
            print(f'{LARANJA}Opcao invalida.{RESET}')
            pausar()


def exportar_json(dados, arquivo):
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f'\n{VERDE}Exportado: {os.path.abspath(arquivo)}{RESET}')
    except Exception as e:
        print(f'\n{LARANJA}Erro ao exportar: {e}{RESET}')


def relatorio_pacientes_por_programa(conn):
    titulo('RELATORIO — PACIENTES POR PROGRAMA', ROXO)
    print('  1-Dentistas do Bem  2-Apolonicas do Bem')
    op = input_opcao('Programa: ', ['1', '2'])
    prog = 'DENTISTAS_DO_BEM' if op == '1' else 'APOLONICAS_DO_BEM'
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pe.nome, pe.cpf, pe.telefone, pe.email,
                   pa.renda_familiar, pa.distancia_km,
                   pa.turno_preferencial, pa.observacoes
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            WHERE pa.programa = :prog
            ORDER BY pe.nome
        """, prog=prog)
        rows = cur.fetchall()
        if not rows:
            print(f'\n{LARANJA}Nenhum paciente neste programa.{RESET}')
            return
        dados = []
        print(f'\n{ROXO}{NEGRITO}{"Nome":<30} {"CPF":<16} {"Turno":<8} {"Renda"}{RESET}')
        linha(ROXO)
        for r in rows:
            dados.append({
                'nome': r[0], 'cpf': r[1], 'telefone': r[2],
                'email': r[3], 'programa': prog,
                'renda_familiar': float(r[4] or 0),
                'distancia_km': float(r[5] or 0),
                'turno_preferencial': r[6],
                'observacoes': r[7],
            })
            print(f'{r[0][:29]:<30} {r[1]:<16} {r[6]:<8} R$ {float(r[4] or 0):>8,.2f}')
        print(f'\n{ROXO}Total: {len(dados)} paciente(s){RESET}')
        if confirmar('Exportar para JSON?'):
            nome_arq = 'dentistas' if op == '1' else 'apolonicas'
            exportar_json(dados, f'relatorio_pacientes_{nome_arq}.json')
    except Exception as e:
        print(f'\n{LARANJA}Erro: {e}{RESET}')


def relatorio_consultas_por_status(conn):
    titulo('RELATORIO — CONSULTAS POR STATUS', ROXO)
    print('  1-AGENDADA  2-REALIZADA  3-CANCELADA  4-FALTA')
    status = STATUS_MAP[input_opcao('Status: ', ['1', '2', '3', '4'])]
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.id_consulta, pe_pac.nome, pe_den.nome,
                   TO_CHAR(c.data_consulta, 'DD/MM/YYYY'),
                   c.horario, c.turno, c.tipo,
                   pa.distancia_km, pa.renda_familiar, c.observacoes
            FROM tdb_Consulta c
            JOIN tdb_Paciente pa ON pa.id_paciente = c.id_paciente
            JOIN tdb_Pessoa pe_pac ON pe_pac.cpf = pa.cpf
            JOIN tdb_Dentista den ON den.cro = c.cro_dentista AND den.cpf = c.cpf_dentista
            JOIN tdb_Pessoa pe_den ON pe_den.cpf = den.cpf
            WHERE c.status = :status
            ORDER BY c.data_consulta DESC
        """, status=status)
        rows = cur.fetchall()
        if not rows:
            print(f'\n{LARANJA}Nenhuma consulta com status {status}.{RESET}')
            return
        dados = []
        print(f'\n{ROXO}{NEGRITO}{"ID":<5} {"Paciente":<25} {"Data":<12} {"Horario":<8} {"Tipo"}{RESET}')
        linha(ROXO)
        for r in rows:
            dados.append({
                'id_consulta': int(r[0]), 'paciente': r[1], 'dentista': r[2],
                'data_consulta': r[3], 'horario': r[4], 'turno': r[5],
                'status': status, 'tipo': r[6],
                'distancia_km': float(r[7] or 0),
                'renda_familiar': float(r[8] or 0),
                'observacoes': r[9],
            })
            print(f'{int(r[0]):<5} {r[1][:24]:<25} {r[3]:<12} {r[4] or "-":<8} {r[6] or "-"}')
        print(f'\n{ROXO}Total: {len(dados)} consulta(s){RESET}')
        if confirmar('Exportar para JSON?'):
            exportar_json(dados, f'relatorio_consultas_{status.lower()}.json')
    except Exception as e:
        print(f'\n{LARANJA}Erro: {e}{RESET}')


def menu_relatorios(conn):
    while True:
        limpar()
        titulo('RELATORIOS', ROXO)
        op = menu_opcao({
            '1': 'Pacientes por programa',
            '2': 'Consultas por status',
            '0': 'Voltar',
        }, 'MENU — RELATORIOS', ROXO)
        if op == '0':
            break
        elif op == '1':
            relatorio_pacientes_por_programa(conn)
            pausar()
        elif op == '2':
            relatorio_consultas_por_status(conn)
            pausar()
        else:
            print(f'{LARANJA}Opcao invalida.{RESET}')
            pausar()