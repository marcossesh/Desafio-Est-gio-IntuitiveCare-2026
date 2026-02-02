import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import zipfile
import shutil

try:
    from src.utils import setup_logger
except ImportError:
    from utils import setup_logger

logger = setup_logger(__name__)

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"

# Cabeçalho para parecer um navegador real e evitar bloqueio
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def obter_links_arquivos(url_base):
    logger.info(f"Acessando: {url_base}")
    try:
        response = requests.get(url_base, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar {url_base}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    links_anos = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            texto = link.text.strip().replace('/', '')
            if href.endswith('/') and texto.isdigit() and len(texto) == 4:
                links_anos.append(texto)
    
    anos_ordenados = sorted(links_anos, reverse=True)
    logger.info(f"Anos encontrados: {anos_ordenados}")

    arquivos_encontrados = []
    
    for ano in anos_ordenados[:2]:
        url_ano = urljoin(url_base, f"{ano}/")
        logger.info(f"Verificando ano: {ano}...")
        
        try:
            resp_ano = requests.get(url_ano, headers=HEADERS, timeout=30)
            soup_ano = BeautifulSoup(resp_ano.text, 'html.parser')
            
            for link in soup_ano.find_all('a'):
                href = link.get('href')
                if href and href.lower().endswith('.zip'):
                    full_url = urljoin(url_ano, href)
                    arquivos_encontrados.append(full_url)
                    
        except Exception as e:
            logger.warning(f"Erro ao ler pasta do ano {ano}: {e}")

    return arquivos_encontrados

def baixar_e_extrair_arquivos(urls, pasta_raw):

    pasta_extracao = os.path.join(pasta_raw, "extracted")
    os.makedirs(pasta_extracao, exist_ok=True)

    for url in urls:
        nome_arquivo = url.split('/')[-1]
        caminho_zip = os.path.join(pasta_raw, nome_arquivo)

        try:
            logger.info(f"Iniciando download: {nome_arquivo}")
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(caminho_zip, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
            
            logger.info(f"Extraindo: {nome_arquivo}")
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_extracao)

        except Exception as e:
            logger.error(f"Erro ao processar {nome_arquivo}: {e}")

if __name__ == "__main__":
    try:
        links = obter_links_arquivos(BASE_URL)
        links_recentes = sorted(links, reverse=True)[:3]
        
        logger.info(f"Encontrados {len(links)} arquivos no total. Selecionando os 3 mais recentes:")
        for l in links_recentes:
            logger.info(f"Selecionado para download: {l}")
        
        baixar_e_extrair_arquivos(links_recentes, "data/raw")
    except Exception as e:
        logger.critical(f"Erro crítico inesperado: {e}")
