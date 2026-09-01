import json
import requests
import os
import unicodedata

DADOS_DIR = r"c:\Users\Marco Antônio\Documents\Chat\AUTOWORK\modules\dados"
MUNICIPIOS_FILE = os.path.join(DADOS_DIR, "municipios_brasil.json")

FUSOS_BR = {
    "AC": "America/Rio_Branco",
    "AL": "America/Maceio",
    "AM": "America/Manaus",
    "AP": "America/Belem",
    "BA": "America/Bahia",
    "CE": "America/Fortaleza",
    "DF": "America/Sao_Paulo",
    "ES": "America/Sao_Paulo",
    "GO": "America/Sao_Paulo",
    "MA": "America/Fortaleza",
    "MG": "America/Sao_Paulo",
    "MS": "America/Campo_Grande",
    "MT": "America/Cuiaba",
    "PA": "America/Belem",
    "PB": "America/Fortaleza",
    "PE": "America/Recife",
    "PI": "America/Fortaleza",
    "PR": "America/Sao_Paulo",
    "RJ": "America/Sao_Paulo",
    "RN": "America/Fortaleza",
    "RO": "America/Porto_Velho",
    "RR": "America/Boa_Vista",
    "RS": "America/Sao_Paulo",
    "SC": "America/Sao_Paulo",
    "SE": "America/Maceio",
    "SP": "America/Sao_Paulo",
    "TO": "America/Araguaina",
}

def baixar_municipios():
    url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
    print("Baixando municípios do IBGE com requests...")
    try:
        response = requests.get(url, headers={"User-Agent": "AUTOWORK-Bot"})
        response.raise_for_status()
        data = response.json()
            
        municipios = {}
        for m in data:
            nome = m["nome"]
            uf = None
            if m.get("microrregiao"):
                uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            elif m.get("regiao-imediata"):
                uf = m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]
            
            if not uf:
                continue
                
            chave = f"{nome.lower()}-{uf.lower()}"
            chave_norm = unicodedata.normalize('NFKD', chave).encode('ASCII', 'ignore').decode('utf-8')
            
            municipios[chave_norm] = {
                "nome": nome,
                "estado": uf,
                "pais": "Brasil",
                "timezone": FUSOS_BR.get(uf, "America/Sao_Paulo")
            }
            
        with open(MUNICIPIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(municipios, f, ensure_ascii=False, indent=2)
            
        print(f"Salvos {len(municipios)} municípios em {MUNICIPIOS_FILE}")
    except Exception as e:
        print(f"Erro ao baixar municípios: {e}")

if __name__ == "__main__":
    baixar_municipios()
