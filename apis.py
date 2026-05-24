# Integração com APIs externas: ViaCEP e API de IA

import re
import datetime

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

from config import API_IA, API_CEP, TIMEOUT_IA, TIMEOUT_CEP
from config import VERDE, LARANJA, AZUL, AMARELO, RESET
from ui import input_validado, validar_cep


def buscar_cep(cep):
    if not REQUESTS_OK:
        print(f'{LARANJA}requests nao instalado.{RESET}')
        return None
    try:
        cep_limpo = re.sub(r'\D', '', cep)
        resp = requests.get(f'{API_CEP}/{cep_limpo}/json/', timeout=TIMEOUT_CEP)
        resp.raise_for_status()
        data = resp.json()
        if data.get('erro'):
            print(f'{LARANJA}CEP nao encontrado.{RESET}')
            return None
        return {
            'logradouro': data.get('logradouro', ''),
            'bairro': data.get('bairro', ''),
            'cidade': data.get('localidade', ''),
            'uf': data.get('uf', ''),
            'cep': data.get('cep', cep),
        }
    except requests.exceptions.Timeout:
        print(f'{LARANJA}Timeout ao consultar ViaCEP.{RESET}')
        return None
    except Exception as e:
        print(f'{LARANJA}Erro ViaCEP: {e}{RESET}')
        return None


def preencher_endereco():
    cep = input_validado(
        'CEP (ENTER para pular): ',
        validar_cep, 'CEP invalido.',
        opcional=True
    )
    if not cep:
        return None, None, None, None, None, None
    print(f'{AMARELO}Consultando ViaCEP...{RESET}')
    dados = buscar_cep(cep)
    if dados:
        print(f'{VERDE}Endereco: {dados["logradouro"]}, {dados["bairro"]} — {dados["cidade"]}/{dados["uf"]}{RESET}')
        logr = dados['logradouro'] or input(f'{AZUL}Logradouro: {RESET}').strip()
        bairro = dados['bairro'] or input(f'{AZUL}Bairro: {RESET}').strip()
        cidade = dados['cidade']
        uf = dados['uf']
    else:
        logr = input(f'{AZUL}Logradouro: {RESET}').strip()
        bairro = input(f'{AZUL}Bairro: {RESET}').strip()
        cidade = input(f'{AZUL}Cidade: {RESET}').strip()
        uf = input(f'{AZUL}UF: {RESET}').strip().upper()
    numero = input(f'{AZUL}Numero: {RESET}').strip()
    return cep, logr, numero, bairro, cidade, uf


def chamar_api_ia(endpoint, payload=None, metodo='GET'):
    if not REQUESTS_OK:
        print(f'{LARANJA}requests nao instalado.{RESET}')
        return None
    try:
        url = f'{API_IA}{endpoint}'
        print(f'{AMARELO}Aguarde — conectando a API de IA...{RESET}')
        if metodo == 'POST':
            resp = requests.post(url, json=payload, timeout=TIMEOUT_IA)
        else:
            resp = requests.get(url, timeout=TIMEOUT_IA)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get('sucesso') is False:
            print(f'\n{LARANJA}Erro da API: {data.get("erro")}{RESET}')
            return None
        return data
    except requests.exceptions.Timeout:
        print(f'\n{LARANJA}Timeout: API demorou mais de {TIMEOUT_IA}s. Tente novamente.{RESET}')
        return None
    except requests.exceptions.ConnectionError:
        print(f'\n{LARANJA}Sem conexao com {API_IA}. Verifique se o Render esta ativo.{RESET}')
        return None
    except requests.exceptions.HTTPError as e:
        print(f'\n{LARANJA}Erro HTTP {e.response.status_code}: {e.response.text[:200]}{RESET}')
        return None
    except Exception as e:
        print(f'\n{LARANJA}Erro inesperado: {e}{RESET}')
        return None


def verificar_api_ia():
    data = chamar_api_ia('/health')
    if not data:
        return False
    status = data.get('status', '?')
    falta = data.get('modelos', {}).get('falta', 'desconhecido')
    arrec = data.get('modelos', {}).get('arrecadacao', 'desconhecido')
    cor = VERDE if status == 'ok' else LARANJA
    print(f'\n{cor}API status: {status}{RESET}')
    print(f'  falta: {falta}')
    print(f'  arrecadacao: {arrec}')
    if 'nao encontrado' in falta or 'nao encontrado' in arrec:
        print(f'\n{LARANJA}Aviso: algum modelo nao foi carregado no Render.{RESET}')
    return status == 'ok'


def prever_falta(conn):
    from pacientes import listar_pacientes
    listar_pacientes(conn)
    try:
        id_pac = int(input(f'\n{AZUL}ID do paciente: {RESET}').strip())
    except ValueError:
        print(f'{LARANJA}ID invalido.{RESET}')
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT pa.distancia_km, pa.renda_familiar,
                   pa.turno_preferencial, pa.programa,
                   (SELECT COUNT(*) FROM tdb_Consulta c2
                    WHERE c2.id_paciente = pa.id_paciente AND c2.status = 'FALTA') AS faltas,
                   (SELECT COUNT(*) FROM tdb_Consulta c3
                    WHERE c3.id_paciente = pa.id_paciente) AS total,
                   pe.nome
            FROM tdb_Paciente pa
            JOIN tdb_Pessoa pe ON pe.cpf = pa.cpf
            WHERE pa.id_paciente = :id
        """, id=id_pac)
        row = cur.fetchone()
    except Exception as e:
        print(f'\n{LARANJA}Erro ao consultar banco: {e}{RESET}')
        return

    if not row:
        print(f'{LARANJA}Paciente nao encontrado.{RESET}')
        return

    dist, renda, turno, prog, faltas, total, nome = row
    print(f'\n{AZUL}Paciente: {nome}{RESET}')

    try:
        dias = int(input(f'{AZUL}Dias ate a consulta: {RESET}').strip())
        if dias < 0:
            raise ValueError
    except ValueError:
        print(f'{LARANJA}Valor invalido. Usando 3 dias.{RESET}')
        dias = 3

    payload = {
        'distanciaKm': float(dist or 0),
        'rendaFamiliar': float(renda or 0),
        'faltasAnteriores': int(faltas or 0),
        'totalConsultas': max(int(total or 1), 1),
        'turnoPref': turno or 'MANHA',
        'turnoConsulta': turno or 'MANHA',
        'diasAteConsulta': max(dias, 0),
        'programa': prog or 'DENTISTAS_DO_BEM',
    }

    data = chamar_api_ia('/predict/falta', payload, 'POST')
    if not data:
        return

    prob = data.get('probabilidadeFalta', 0)
    risco = data.get('risco', '-')
    cor = {'ALTO': LARANJA, 'MEDIO': AMARELO, 'BAIXO': VERDE}.get(risco, RESET)
    print(f'\n  Probabilidade: {cor}{prob * 100:.1f}%{RESET}')
    print(f'  Risco: {cor}{risco}{RESET}')
    print(f'  Classe: {data.get("classePrevista", "-")}')
    print(f'  Recomendacao: {data.get("recomendacao", "-")}')


def prever_arrecadacao():
    try:
        meta = float(input(f'{AZUL}Meta R$: {RESET}').strip())
        if meta <= 0:
            raise ValueError
    except ValueError:
        print(f'{LARANJA}Meta invalida. Deve ser um valor positivo.{RESET}')
        return

    try:
        duracao = int(input(f'{AZUL}Duracao em dias: {RESET}').strip())
        if duracao <= 0:
            raise ValueError
    except ValueError:
        print(f'{LARANJA}Duracao invalida.{RESET}')
        return

    try:
        mes = int(input(f'{AZUL}Mes de inicio (1-12): {RESET}').strip())
        if not 1 <= mes <= 12:
            raise ValueError
    except ValueError:
        print(f'{LARANJA}Mes invalido. Informe um valor entre 1 e 12.{RESET}')
        return

    try:
        anteriores = int(input(f'{AZUL}Campanhas anteriores: {RESET}').strip())
        voluntarios = int(input(f'{AZUL}Voluntarios: {RESET}').strip())
        doacoes = int(input(f'{AZUL}Estimativa de doacoes: {RESET}').strip())
        if anteriores < 0 or voluntarios < 0 or doacoes < 0:
            raise ValueError
    except ValueError:
        print(f'{LARANJA}Valores invalidos. Informe numeros inteiros positivos.{RESET}')
        return

    payload = {
        'metaValor': meta,
        'duracaoDias': duracao,
        'mesInicio': mes,
        'anoInicio': datetime.date.today().year,
        'campanhasAnteriores': anteriores,
        'qtdVoluntarios': max(voluntarios, 1),
        'qtdDoacoes': max(doacoes, 1),
    }

    data = chamar_api_ia('/predict/arrecadacao', payload, 'POST')
    if not data:
        return

    tend = data.get('tendencia', '-')
    cor = {'ALTA': VERDE, 'ESTAVEL': AZUL, 'BAIXA': LARANJA}.get(tend, RESET)
    print(f'\n  Valor previsto: {VERDE}R$ {data.get("valorPrevisto", 0):,.2f}{RESET}')
    print(f'  % da meta: {data.get("pctMeta", 0) * 100:.1f}%')
    print(f'  Tendencia: {cor}{tend}{RESET}')
    print(f'  Confianca: {data.get("confianca", 0) * 100:.0f}%')
    print(f'  Recomendacao: {data.get("recomendacao", "-")}')