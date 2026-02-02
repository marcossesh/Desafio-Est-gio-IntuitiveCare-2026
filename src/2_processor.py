import pandas as pd
import os
import glob
import re
try:
    from src.utils import setup_logger, zip_file
except ImportError:
    from utils import setup_logger, zip_file

logger = setup_logger(__name__)


# Mapeamento de possíveis nomes de colunas encontrados nos arquivos da ANS
COLUM_MAP = {
    'CNPJ': ['cnpj', 'cnpj_operadora', 'nr_cnpj', 'CNPJ'],
    'RazaoSocial': ['razao_social', 'nm_razao_social', 'Razao Social', 'RAZAO_SOCIAL'],
    'ValorDespesas': ['vl_saldo_final', 'valor', 'VL_SALDO_FINAL', 'DESPESA'],
    'RegAns': ['reg_ans', 'REG_ANS', 'registro_ans']
}

def normalizar_colunas(df):

    rename_dict = {}
    for padrao, aliases in COLUM_MAP.items():
        for col in df.columns:
            if col in aliases or col.upper() in [a.upper() for a in aliases]:
                rename_dict[col] = padrao
    return df.rename(columns=rename_dict)

def limpar_dados_criticos(df):
    logger.info("Iniciando limpeza crítica de inconsistências...")

    df = df.sort_values(by=['Ano', 'Trimestre'], ascending=False)
    
    mapping_razao = df.drop_duplicates('CNPJ').set_index('CNPJ')['RazaoSocial'].to_dict()
    
    df['RazaoSocial'] = df['CNPJ'].map(mapping_razao)

    # Fix: Replace comma with dot for brazilian decimal format before conversion
    df['ValorDespesas'] = df['ValorDespesas'].astype(str).str.replace(',', '.', regex=False)
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce').fillna(0)
    
    df = df.dropna(subset=['CNPJ', 'RazaoSocial'])
    
    return df

    return df

def consolidar_por_periodo(df):
    logger.info("Agrupando despesas por operadora e período...")
    return df.groupby(['CNPJ', 'RazaoSocial', 'Ano', 'Trimestre']).agg({
        'ValorDespesas': 'sum'
    }).reset_index()

def extrair_metadados(nome_arquivo):

    padrao = re.search(r'(\d)T(\d{4})', nome_arquivo, re.IGNORECASE)
    if padrao:
        return padrao.group(2), padrao.group(1)
    return "2025", "1"

def processar_arquivos(diretorio_origem):
    arquivos = glob.glob(os.path.join(diretorio_origem, "**/*.*"), recursive=True)
    lista_dfs = []

    for arquivo in arquivos:
        nome_base = os.path.basename(arquivo)
        logger.info(f"Processando arquivo: {nome_base}")
        
        try:
            ano, trimestre = extrair_metadados(nome_base)

            if arquivo.endswith('.csv'):
                df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin-1')
            elif arquivo.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(arquivo)
            else:
                continue

            df = normalizar_colunas(df)
            
            if 'CD_CONTA_CONTABIL' in df.columns:
                # Filtrar apenas CONTAS ANALÍTICAS (Nível 9) do grupo 411 para evitar duplicação de hierarquia (Ex: 411 + 4111...)
                # Exemplo de conta analítica: 411512061 (9 dígitos)
                df['CD_CONTA_CONTABIL'] = df['CD_CONTA_CONTABIL'].astype(str)
                df = df[
                    (df['CD_CONTA_CONTABIL'].str.startswith('411')) & 
                    (df['CD_CONTA_CONTABIL'].str.len() == 9)
                ]
            
            #Se não tem CNPJ mas tem RegAns, usa RegAns
            if 'CNPJ' not in df.columns and 'RegAns' in df.columns:
                df['CNPJ'] = df['RegAns']
                if 'RazaoSocial' not in df.columns:
                    df['RazaoSocial'] = "Operadora " + df['RegAns'].astype(str)

            df['Ano'] = ano
            df['Trimestre'] = trimestre
            
            colunas_finais = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
            
            colunas_presentes = [c for c in colunas_finais if c in df.columns]
            if len(colunas_presentes) == len(colunas_finais):
                lista_dfs.append(df[colunas_finais])
            else:
                logger.warning(f"Arquivo {nome_base} ignorado. Colunas faltantes: {set(colunas_finais) - set(df.columns)}")
                
        except Exception as e:
            logger.error(f"Falha ao processar {arquivo}: {e}")

    if not lista_dfs:
        return pd.DataFrame()
    
    df_consolidado = pd.concat(lista_dfs, ignore_index=True)
    df_limpo = limpar_dados_criticos(df_consolidado)
    return consolidar_por_periodo(df_limpo)



if __name__ == "__main__":


    DIRETORIO_RAW = "data/raw/extracted"
    df_final = processar_arquivos(DIRETORIO_RAW)
    
    if not df_final.empty:
        os.makedirs("data/processed", exist_ok=True)

        caminho_csv = "data/processed/consolidado_despesas.csv"
        df_final.to_csv(caminho_csv, index=False, encoding='utf-8')
        logger.info(f"Arquivo consolidado gerado com sucesso: {caminho_csv}")
        
        caminho_zip = "data/processed/consolidado_despesas.zip"
        zip_file(caminho_csv, caminho_zip)
        logger.info("Fase 1 concluída com sucesso!")
    else:
        logger.error("Nenhum dado processado.")
