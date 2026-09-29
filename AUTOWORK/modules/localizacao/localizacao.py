import json
import os
import unicodedata
from functools import lru_cache
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

class LocalizacaoError(RuntimeError):
    pass


def localizar_usuario(timeout: int = 5) -> dict:
    """Localiza o usuário pela geolocalização do IP (ip-api.com).

    Retorna estrutura compatível com os módulos de clima e tempo:
    {sucesso, acao, dados, mensagem, erro}.
    """
    url = (
        "http://ip-api.com/json/"
        "?fields=status,city,regionName,country,lat,lon,timezone&lang=pt-BR"
    )
    try:
        req = Request(url, headers={"User-Agent": "AUTOWORK/1.0"})
        with urlopen(req, timeout=timeout) as resposta:
            dados = json.loads(resposta.read())

        if dados.get("status") != "success" or not dados.get("city"):
            raise LocalizacaoError("Não foi possível determinar a localização.")

        cidade = dados["city"]
        regiao = dados.get("regionName", "")
        pais = dados.get("country", "")

        partes = [cidade] + [p for p in (regiao, pais) if p]
        mensagem = "Você está em " + ", ".join(partes) + "."

        return {
            "sucesso": True,
            "acao": "consultar_localizacao",
            "dados": {
                "cidade": cidade,
                "regiao": regiao,
                "pais": pais,
                "latitude": dados.get("lat"),
                "longitude": dados.get("lon"),
                "timezone": dados.get("timezone"),
            },
            "mensagem": mensagem,
            "erro": None,
        }
    except LocalizacaoError as e:
        return {
            "sucesso": False,
            "acao": "consultar_localizacao",
            "dados": None,
            "mensagem": "Não consegui obter a sua localização.",
            "erro": str(e),
        }
    except Exception:
        return {
            "sucesso": False,
            "acao": "consultar_localizacao",
            "dados": None,
            "mensagem": "Não consegui obter a sua localização.",
            "erro": "api_indisponivel",
        }

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS_DIR = os.path.join(BASE_DIR, "dados")

def carregar_json(caminho: str) -> dict:
    if not os.path.exists(caminho):
        return {}
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

MUNICIPIOS = carregar_json(os.path.join(DADOS_DIR, "municipios_brasil.json"))
CAPITAIS = carregar_json(os.path.join(DADOS_DIR, "capitais_internacionais.json"))
PAISES_CAPITAIS = carregar_json(os.path.join(DADOS_DIR, "paises_capitais.json"))
ALIASES = carregar_json(os.path.join(DADOS_DIR, "aliases.json"))

def normalizar_nome(nome: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nome = nome.lower().strip()
    return unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('utf-8')


def _normalizar_referencia_capital(local_norm: str) -> str:
    """Remove o prefixo de referência usado em frases como 'capital do Japão'."""
    for prefixo in ("capital do ", "capital da ", "capital de ", "capital dos ", "capital das "):
        if local_norm.startswith(prefixo):
            return local_norm[len(prefixo):].strip()
    return local_norm


def _localizacao_capital(registro: dict) -> dict:
    """Converte um registro país-capital no contrato comum de localidades."""
    return {
        "nome": registro["capital"],
        "pais": registro["pais"],
        "latitude": registro["lat"],
        "longitude": registro["lon"],
        "timezone": registro["timezone"],
        "capital": True,
    }

@lru_cache(maxsize=128)
def localizar_nominatim(local: str) -> tuple[float, float]:
    """Busca latitude e longitude no Nominatim."""
    url = "https://nominatim.openstreetmap.org/search?" + urlencode({
        "q": local, "format": "json", "limit": 1
    })
    try:
        req = Request(url, headers={"User-Agent": "AUTOWORK/1.0"})
        with urlopen(req, timeout=5) as resposta:
            dados = json.loads(resposta.read())
            
        if not dados:
            return None, None
            
        primeiro = dados[0]
        return float(primeiro["lat"]), float(primeiro["lon"])
    except Exception:
        return None, None

@lru_cache(maxsize=128)
def resolver_localidade(local_str: str) -> dict:
    """
    Resolve uma string de localidade para um dicionário padronizado:
    {nome, estado (opcional), pais, latitude, longitude, timezone}
    """
    if not local_str or not local_str.strip():
        raise LocalizacaoError("Localidade não informada.")
        
    local_norm = _normalizar_referencia_capital(normalizar_nome(local_str))

    # Países são resolvidos pela capital nacional. Essa consulta vem antes
    # dos aliases históricos que alguns países usam como atalho para cidades.
    if local_norm in PAISES_CAPITAIS:
        return _localizacao_capital(PAISES_CAPITAIS[local_norm])
    
    # 1. Verifica aliases
    if local_norm in ALIASES:
        local_norm = ALIASES[local_norm]

    if local_norm in PAISES_CAPITAIS:
        return _localizacao_capital(PAISES_CAPITAIS[local_norm])
        
    # 2. Tenta capitais internacionais
    if local_norm in CAPITAIS:
        cap = CAPITAIS[local_norm]
        return {
            "nome": cap["nome"],
            "pais": cap["pais"],
            "latitude": cap["lat"],
            "longitude": cap["lon"],
            "timezone": cap["timezone"],
            "capital": True,
        }
        
    # 3. Tenta municípios do Brasil
    # Pode ser "campinas", "campinas-sp" ou "campinas sp"
    if "-" in local_norm:
        cidade_uf = local_norm
    elif local_norm.endswith(tuple(f" {uf}" for uf in ["ac","al","am","ap","ba","ce","df","es","go","ma","mg","ms","mt","pa","pb","pe","pi","pr","rj","rn","ro","rr","rs","sc","se","sp","to"])):
        partes = local_norm.rsplit(" ", 1)
        cidade_uf = f"{partes[0]}-{partes[1]}"
    else:
        # Tenta achar a cidade sem estado (busca no dict, o primeiro que bater)
        encontrados = [k for k in MUNICIPIOS.keys() if k.startswith(f"{local_norm}-")]
        if encontrados:
            # Prioriza capitais se houver ambiguidade (ex: "sao paulo" -> "sao paulo-sp")
            # Mas geralmente só tem 1 ou pegamos o primeiro (se for cidade homônima, o usuário precisa ser específico)
            cidade_uf = encontrados[0]
        else:
            cidade_uf = None
            
    if cidade_uf and cidade_uf in MUNICIPIOS:
        mun = MUNICIPIOS[cidade_uf]
        lat, lon = localizar_nominatim(f"{mun['nome']}, {mun['estado']}, Brasil")
        if not lat:
            # Fallback se nominatim falhar, usa uma lat/lon aproximada do estado? 
            # (Ou só levanta erro de rede, o ideal é não levantar erro logo de cara)
            lat, lon = 0.0, 0.0 # Será tratado pelo serviço que precisa de lat/lon reais
            
        return {
            "nome": mun["nome"],
            "estado": mun["estado"],
            "pais": mun["pais"],
            "timezone": mun["timezone"],
            "latitude": lat,
            "longitude": lon
        }
        
    # 4. Fallback total Nominatim + adivinhar timezone? 
    # Para o AUTOWORK atual, se não está na base, retornaremos erro amigável, pois queremos controle sobre as localidades suportadas.
    raise LocalizacaoError(f"Localidade '{local_str}' não encontrada na base de dados.")
