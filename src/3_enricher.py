import pandas as pd
import requests
from validate_docbr import CNPJ
import logging
import os
import zipfile

logger = logging.getLogger(__name__)
cnpj_validator = CNPJ()

CADASTRO_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

def baixar_cadastro_ans(url, destino):
    logger.info("Baixando cadastro de operadoras ativas...")
    response = requests.get(url, timeout=30)
    with open(destino, 'wb') as f:
        f.write(response.content)

    # A ANS costuma usar ';' ou ',' e encoding latin-1
    return pd.read_csv(destino, sep=None, engine='python', encoding='latin-1')

def validar_e_corrigir(df_consolidado, df_cadastral):
    logger.info("Iniciando validação e correção de fallbacks (Otimizado via Merge)...")
    
    df_consolidado['CNPJ_clean'] = df_consolidado['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    
    df_cadastral['REGISTRO_STR'] = df_cadastral['REGISTRO_OPERADORA'].astype(str)
    df_cadastral['CNPJ_STR'] = df_cadastral['CNPJ'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(14)
    
    merged = df_consolidado.merge(
        df_cadastral[['REGISTRO_STR', 'CNPJ_STR', 'Razao_Social', 'UF', 'Modalidade']],
        left_on='CNPJ_clean',
        right_on='REGISTRO_STR',
        how='left'
    )
    
    # Identificar onde houve match pelo Registro ANS
    match_cond = merged['REGISTRO_STR'].notna()
    
    merged['CNPJ'] = merged['CNPJ'].astype(str)
    merged.loc[match_cond, 'CNPJ'] = merged.loc[match_cond, 'CNPJ_STR']
    merged.loc[match_cond, 'RazaoSocial'] = merged.loc[match_cond, 'Razao_Social']

    cnpj_to_uf = df_cadastral.set_index('CNPJ_STR')['UF'].to_dict()
    cnpj_to_razao = df_cadastral.set_index('CNPJ_STR')['Razao_Social'].to_dict()
    
    current_cnpjs = merged['CNPJ'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(14)
    
    cnpj_to_modalidade = df_cadastral.set_index('CNPJ_STR')['Modalidade'].to_dict()
    merged['UF'] = merged['UF'].fillna(current_cnpjs.map(cnpj_to_uf))
    merged['Modalidade'] = merged['Modalidade'].fillna(current_cnpjs.map(cnpj_to_modalidade))
    
    df = merged.drop(columns=['CNPJ_clean', 'REGISTRO_STR', 'CNPJ_STR', 'Razao_Social'])
    
    df['cnpj_valido'] = df['CNPJ'].astype(str).apply(cnpj_validator.validate)
    df = df[df['cnpj_valido'] == True].copy()
    
    df = df[df['ValorDespesas'] >= 0]
    df = df[df['RazaoSocial'].str.strip() != ""]

    df = df.dropna(subset=['UF'])
    
    return df.drop(columns=['cnpj_valido'])

def gerar_agregados(df_enriquecido):
    logger.info("Gerando agregações estatísticas...")
    
    agregado = df_enriquecido.groupby(['CNPJ', 'RazaoSocial', 'UF', 'Modalidade']).agg({
        'ValorDespesas': ['sum', 'mean', 'std']
    })
    
    agregado.columns = ['Total_Despesas', 'Media_Trimestral', 'Desvio_Padrao']
    return agregado.sort_values(by='Total_Despesas', ascending=False).reset_index()

def zipar_consolidado(caminho_csv, caminho_zip):
    logger.info(f"Compactando arquivo para: {caminho_zip}")
    with zipfile.ZipFile(caminho_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(caminho_csv, arcname=os.path.basename(caminho_csv))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    CAMINHO_CONSOLIDADO = "data/processed/consolidado_despesas.csv"
    CAMINHO_CADASTRO = "data/raw/Relatorio_Cadop.csv"
    
    if not os.path.exists(CAMINHO_CONSOLIDADO):
        logger.error(f"Arquivo consolidado não encontrado: {CAMINHO_CONSOLIDADO}")
        exit(1)
        
    df_consolidado = pd.read_csv(CAMINHO_CONSOLIDADO)
    
    try:
        df_cadastro = baixar_cadastro_ans(CADASTRO_URL, CAMINHO_CADASTRO)
    except Exception as e:
        logger.error(f"Erro ao baixar cadastro: {e}")
        exit(1)
        
    df_enriquecido = validar_e_corrigir(df_consolidado, df_cadastro)
    
    df_agregado = gerar_agregados(df_enriquecido)
    
    if not df_agregado.empty:
        os.makedirs("data/enriched", exist_ok=True)
        
        caminho_csv = "data/enriched/despesas_agregadas.csv"
        df_agregado.to_csv(caminho_csv, index=False, encoding='utf-8')
        logger.info(f"Arquivo agregado gerado com sucesso: {caminho_csv}")
        
        caminho_zip = "data/enriched/despesas_agregadas.zip"
        zipar_consolidado(caminho_csv, caminho_zip)
        logger.info("Fase 2 concluída com sucesso!")
    else:
        logger.warning("Nenhum dado restou após a validação.")