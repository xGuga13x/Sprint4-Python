# CRUD de Pacientes com validações completas

import oracledb
from config import VERDE, LARANJA, AZUL, RESET, NEGRITO
from ui import (
    limpar, titulo, pausar, confirmar, menu_opcao,
    validar_cpf, formatar_cpf, validar_telefone,
    validar_data, input_validado, input_opcao, linha,
)
from db import proximo_id
from apis import preencher_endereco

TURNO_MAP = {'1': 'MANHA', '2': 'TARDE', '3': 'NOITE'}
PROG_MAP = {'1': 'DENTISTAS_DO_BEM', '2': 'APOLONICAS_DO_BEM'}


def _cpf_existe_pessoa(cur, cpf):
    cur.execute('SELECT 1 FROM tdb_Pessoa WHERE cpf = :cpf', cpf=cpf)
    return cur.fetchone() is not None


def _cpf_existe_paciente(cur, cpf):
    cur.execute('SELECT 1 FROM tdb_Paciente WHERE cpf = :cpf', cpf=cpf)
    return cur.fetchone() is not None


def _paciente_existe_id(cur, id_pac):
    cur.execute('SELECT 1 FROM tdb_Paciente WHERE id_paciente = :id', id=id_pac)
    return cur.fetchone() is not None


def _prog_label(prog):
    return 'Dentistas do Bem' if prog == 'DENTISTAS_DO_BEM' else 'Apolonicas do Bem'


def _pedir_id(msg):
    while True:
        try:
            return int(input(msg).strip())
        except ValueError:
            print(f'{LARANJA}ID invalido. Informe apenas numeros.{RESET}')


def _pedir_float(msg, atual=None):
    label = f' [{atual}]' if atual is not None else ''
    while True:
        try:
            s = input(f'{AZUL}{msg}{label}: {RESET}').strip()
            val = float(s) if s else float(atual or 0)
            if val < 0:
                print(f'{LARANJA}Valor nao pode ser negativo.{RESET}')
                continue
            return val
        except ValueError:
            print(f'{LARANJA}Valor invalido. Use apenas numeros.{RESET}')


def listar_pacientes(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pa.id_paciente, pe.nome, pe.cpf,
                   pa.programa, pa.turno_preferencial
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            ORDER BY pe.nome
        """)
        rows = cur.fetchall()
        if not rows:
            print(f'\n{LARANJA}Nenhum paciente cadastrado.{RESET}')
            return
        print(f'\n{VERDE}{NEGRITO}{"ID":<5} {"Nome":<30} {"CPF":<16} {"Programa":<20} {"Turno"}{RESET}')
        linha()
        for r in rows:
            print(f'{r[0]:<5} {r[1]:<30} {r[2]:<16} {_prog_label(r[3]):<20} {r[4]}')
    except Exception as e:
        print(f'{LARANJA}Erro ao listar pacientes: {e}{RESET}')


def buscar_paciente(conn):
    nome = input(f'{AZUL}Nome para buscar: {RESET}').strip()
    if len(nome) < 2:
        print(f'{LARANJA}Informe ao menos 2 caracteres.{RESET}')
        return
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pa.id_paciente, pe.nome, pe.cpf, pe.telefone,
                   pa.programa, pa.renda_familiar, pa.distancia_km,
                   pa.turno_preferencial, pa.observacoes,
                   pe.logradouro, pe.numero, pe.bairro, pe.cidade, pe.uf
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            WHERE UPPER(pe.nome) LIKE UPPER(:nome)
            ORDER BY pe.nome
        """, nome=f'%{nome}%')
        rows = cur.fetchall()
        if not rows:
            print(f'\n{LARANJA}Nenhum resultado para "{nome}".{RESET}')
            return
        for r in rows:
            end = f'{r[9]}, {r[10]} - {r[11]}, {r[12]}/{r[13]}' if r[9] else '-'
            print(f'\n  ID: {r[0]} | Nome: {r[1]} | CPF: {r[2]}')
            print(f'  Tel: {r[3]} | Prog: {_prog_label(r[4])} | Turno: {r[7]}')
            print(f'  Renda: R$ {float(r[5] or 0):,.2f} | Dist: {r[6]} km')
            print(f'  End: {end} | Obs: {r[8] or "-"}')
    except Exception as e:
        print(f'{LARANJA}Erro ao buscar: {e}{RESET}')


def inserir_paciente(conn):
    titulo('NOVO PACIENTE', VERDE)
    cur = conn.cursor()

    while True:
        nome = input(f'{AZUL}Nome completo: {RESET}').strip()
        if len(nome) < 3:
            print(f'{LARANJA}Informe ao menos 3 caracteres.{RESET}')
        elif not all(c.isalpha() or c.isspace() for c in nome):
            print(f'{LARANJA}Use apenas letras e espacos.{RESET}')
        else:
            break

    pessoa_existente = False
    while True:
        cpf = formatar_cpf(input_validado('CPF: ', validar_cpf, 'CPF invalido. Informe 11 digitos numericos.'))
        if _cpf_existe_paciente(cur, cpf):
            print(f'{LARANJA}CPF ja cadastrado como paciente.{RESET}')
        elif _cpf_existe_pessoa(cur, cpf):
            print(f'{LARANJA}CPF ja existe com outro perfil. Apenas o vinculo de paciente sera criado.{RESET}')
            pessoa_existente = True
            break
        else:
            break

    data_nasc = input_validado('Nascimento (DD/MM/AAAA): ', validar_data, 'Data invalida. Use DD/MM/AAAA.')
    telefone = input_validado('Telefone: ', validar_telefone, 'Telefone invalido. Informe 8 a 11 digitos.')

    while True:
        email = input(f'{AZUL}Email (opcional, ENTER para pular): {RESET}').strip() or None
        if email and ('@' not in email or '.' not in email.split('@')[-1]):
            print(f'{LARANJA}Email invalido.{RESET}')
        else:
            break

    cep, logr, numero, bairro, cidade, uf = preencher_endereco()

    print(f'\n{LARANJA}Programa:  1-Dentistas do Bem  2-Apolonicas do Bem{RESET}')
    programa = PROG_MAP[input_opcao('Escolha: ', ['1', '2'])]

    renda = _pedir_float('Renda familiar R$ (0 se nao informar)')
    distancia = _pedir_float('Distancia ate a clinica km (0 se nao informar)')

    print(f'{LARANJA}Turno:  1-MANHA  2-TARDE  3-NOITE{RESET}')
    turno = TURNO_MAP[input_opcao('Turno: ', ['1', '2', '3'])]
    obs = input(f'{AZUL}Observacoes (opcional): {RESET}').strip() or None

    print(f'\n{VERDE}--- Resumo ---{RESET}')
    print(f'  Nome: {nome}')
    print(f'  CPF: {cpf}')
    print(f'  Nasc: {data_nasc}')
    print(f'  Programa: {programa}')
    print(f'  Renda: R$ {renda:,.2f} | Distancia: {distancia} km')
    print(f'  Turno: {turno}')
    if logr:
        print(f'  Endereco: {logr}, {numero} - {bairro}, {cidade}/{uf}')

    if not confirmar('Confirmar cadastro?'):
        print(f'{LARANJA}Cadastro cancelado.{RESET}')
        return

    try:
        id_pac = proximo_id(conn, 'tdb_Paciente', 'id_paciente')

        if not pessoa_existente:
            cur.execute("""
                INSERT INTO tdb_Pessoa
                    (cpf, nome, data_nasc, telefone, email, cep,
                     logradouro, numero, bairro, cidade, uf, ativo, dt_cadastro)
                VALUES (:cpf, :nome, TO_DATE(:nasc, 'DD/MM/YYYY'), :tel, :email,
                        :cep, :logr, :num, :bairro, :cidade, :uf, 'S', SYSDATE)
            """, cpf=cpf, nome=nome, nasc=data_nasc, tel=telefone,
                 email=email, cep=cep, logr=logr, num=numero,
                 bairro=bairro, cidade=cidade, uf=uf)

        cur.execute("""
            INSERT INTO tdb_Paciente
                (id_paciente, cpf, programa, renda_familiar,
                 distancia_km, turno_preferencial, observacoes)
            VALUES (:id, :cpf, :prog, :renda, :dist, :turno, :obs)
        """, id=id_pac, cpf=cpf, prog=programa,
             renda=renda, dist=distancia, turno=turno, obs=obs)

        conn.commit()
        print(f'\n{VERDE}Paciente cadastrado! ID: {id_pac}{RESET}')

    except oracledb.IntegrityError as e:
        conn.rollback()
        erro = str(e)
        if 'PK_TDB_PESSOA' in erro or 'UK_TDB_PACIENTE_CPF' in erro:
            print(f'\n{LARANJA}CPF ja existe no banco.{RESET}')
        elif 'PK_TDB_PACIENTE' in erro:
            print(f'\n{LARANJA}ID duplicado. Tente novamente.{RESET}')
        else:
            print(f'\n{LARANJA}Erro de integridade: {erro}{RESET}')
    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao cadastrar: {e}{RESET}')


def alterar_paciente(conn):
    titulo('ALTERAR PACIENTE', LARANJA)
    listar_pacientes(conn)

    id_pac = _pedir_id(f'\n{AZUL}ID do paciente (0 para cancelar): {RESET}')
    if id_pac == 0:
        return

    try:
        cur = conn.cursor()
        if not _paciente_existe_id(cur, id_pac):
            print(f'{LARANJA}Paciente ID {id_pac} nao encontrado.{RESET}')
            return

        cur.execute("""
            SELECT pe.nome, pe.telefone, pe.email, pa.programa,
                   pa.renda_familiar, pa.distancia_km,
                   pa.turno_preferencial, pa.observacoes, pe.cpf
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            WHERE pa.id_paciente = :id
        """, id=id_pac)
        nome, tel, email, prog, renda, dist, turno, obs, cpf = cur.fetchone()

        print(f'{AZUL}ENTER para manter o valor atual.{RESET}\n')

        while True:
            novo_tel = input(f'{AZUL}Telefone [{tel}]: {RESET}').strip() or tel
            if not validar_telefone(novo_tel):
                print(f'{LARANJA}Telefone invalido.{RESET}')
            else:
                break

        while True:
            novo_email = input(f'{AZUL}Email [{email or ""}]: {RESET}').strip() or email
            if novo_email and ('@' not in novo_email or '.' not in novo_email.split('@')[-1]):
                print(f'{LARANJA}Email invalido.{RESET}')
            else:
                break

        print(f'{LARANJA}Programa atual: {prog}  1-Dentistas  2-Apolonicas  ENTER manter{RESET}')
        op_prog = input(f'{AZUL}Novo programa: {RESET}').strip()
        novo_prog = PROG_MAP.get(op_prog, prog)

        nova_renda = _pedir_float(f'Renda [R$ {float(renda or 0):,.2f}]', renda)
        nova_dist = _pedir_float(f'Distancia km [{dist or 0}]', dist)

        print(f'{LARANJA}Turno atual: {turno}  1-MANHA  2-TARDE  3-NOITE  ENTER manter{RESET}')
        op_turno = input(f'{AZUL}Novo turno: {RESET}').strip()
        novo_turno = TURNO_MAP.get(op_turno, turno)
        nova_obs = input(f'{AZUL}Observacoes [{obs or ""}]: {RESET}').strip() or obs

        if not confirmar('Confirmar alteracoes?'):
            print(f'{LARANJA}Alteracao cancelada.{RESET}')
            return

        cur.execute(
            'UPDATE tdb_Pessoa SET telefone = :tel, email = :email WHERE cpf = :cpf',
            tel=novo_tel, email=novo_email, cpf=cpf,
        )
        cur.execute("""
            UPDATE tdb_Paciente SET
                programa = :prog, renda_familiar = :renda,
                distancia_km = :dist, turno_preferencial = :turno, observacoes = :obs
            WHERE id_paciente = :id
        """, prog=novo_prog, renda=nova_renda, dist=nova_dist,
             turno=novo_turno, obs=nova_obs, id=id_pac)
        conn.commit()
        print(f'\n{VERDE}Paciente atualizado!{RESET}')

    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao alterar: {e}{RESET}')


def excluir_paciente(conn):
    titulo('EXCLUIR PACIENTE', LARANJA)
    listar_pacientes(conn)

    id_pac = _pedir_id(f'\n{AZUL}ID do paciente (0 para cancelar): {RESET}')
    if id_pac == 0:
        return

    try:
        cur = conn.cursor()
        if not _paciente_existe_id(cur, id_pac):
            print(f'{LARANJA}Paciente ID {id_pac} nao encontrado.{RESET}')
            return

        cur.execute("""
            SELECT pe.nome, pe.cpf FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            WHERE pa.id_paciente = :id
        """, id=id_pac)
        nome, cpf = cur.fetchone()

        cur.execute('SELECT COUNT(*) FROM tdb_Consulta WHERE id_paciente = :id', id=id_pac)
        qtd = cur.fetchone()[0]
        if qtd > 0:
            print(f'\n{LARANJA}ATENCAO: {qtd} consulta(s) vinculada(s) serao removidas junto.{RESET}')

        print(f'\n{LARANJA}Paciente: {nome} | CPF: {cpf}{RESET}')
        if not confirmar('Confirmar exclusao?'):
            print(f'{LARANJA}Cancelado.{RESET}')
            return

        cur.execute('DELETE FROM tdb_Pessoa WHERE cpf = :cpf', cpf=cpf)
        conn.commit()
        print(f'\n{VERDE}Paciente excluido.{RESET}')

    except Exception as e:
        conn.rollback()
        print(f'\n{LARANJA}Erro ao excluir: {e}{RESET}')


def menu_pacientes(conn):
    while True:
        limpar()
        titulo('GESTAO DE PACIENTES', VERDE)
        op = menu_opcao({
            '1': 'Listar todos',
            '2': 'Buscar por nome',
            '3': 'Novo paciente',
            '4': 'Alterar paciente',
            '5': 'Excluir paciente',
            '0': 'Voltar',
        }, 'MENU — PACIENTES')
        if op == '0':
            break
        elif op == '1':
            listar_pacientes(conn)
            pausar()
        elif op == '2':
            buscar_paciente(conn)
            pausar()
        elif op == '3':
            inserir_paciente(conn)
            pausar()
        elif op == '4':
            alterar_paciente(conn)
            pausar()
        elif op == '5':
            excluir_paciente(conn)
            pausar()
        else:
            print(f'{LARANJA}Opcao invalida.{RESET}')
            pausar()