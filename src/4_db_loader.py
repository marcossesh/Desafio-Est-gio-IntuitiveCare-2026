import pandas as pd
from sqlalchemy import create_engine, text
import logging
import io
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuração da conexão (Use variáveis de ambiente para ser sênior!)
DB_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/nome_banco")

def criar_schema(engine):
    """Cria as tabelas usando DDL via SQLAlchemy."""
    logger.info("Criando schema do banco de dados...")
    with engine.connect() as conn:
        # Tabela de Operadoras (Dimensão)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS operadoras (
                cnpj VARCHAR(14) PRIMARY KEY,
                razao_social VARCHAR(255),
                modalidade VARCHAR(100),
                uf CHAR(2)
            );
        """))
        
        # Tabela de Despesas (Fato Temporal)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS despesas_consolidadas (
                id SERIAL PRIMARY KEY,
                cnpj VARCHAR(14) REFERENCES operadoras(cnpj),
                ano INT,
                trimestre INT,
                valor_despesa DECIMAL(18,2)
            );
        """))
        # Drop das tabelas para garantir estado limpo se necessário? 
        # O user pediu CREATE antes de COPY. IF EXISTS evita erro.
        # Vamos assumir que se já existe, podemos truncar para evitar duplicação em carga full
        conn.execute(text("TRUNCATE TABLE despesas_consolidadas, operadoras RESTART IDENTITY CASCADE;"))
        conn.commit()

def fast_copy_to_db(df, table_name, engine, columns=None):
    """Usa o comando COPY do Postgres para carga ultra-rápida."""
    logger.info(f"Carregando {len(df)} linhas na tabela {table_name}...")
    
    # Prepara o DataFrame em memória como um arquivo CSV
    output = io.StringIO()
    df.to_csv(output, index=False, header=False, sep='\t') # Tab separated é mais seguro que virgula p/ strings
    output.seek(0)
    
    # Pega a conexão crua do driver psycopg2
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()
    try:
        # columns deve ser uma tupla de strings, ex: ('col1', 'col2')
        cursor.copy_from(output, table_name, sep='\t', null="", columns=columns)
        raw_conn.commit()
    except Exception as e:
        logger.error(f"Erro no COPY para {table_name}: {e}")
        raw_conn.rollback()
        raise
    finally:
        cursor.close()
        raw_conn.close()

if __name__ == "__main__":
    try:
        engine = create_engine(DB_URL)
        criar_schema(engine)
        
        # 1. Carregar Operadoras (Dimensão)
        # Usamos o enriched para garantir modalidade/uf corretos e filtrados
        logger.info("Lendo dados de operadoras...")
        df_agregado = pd.read_csv("data/enriched/despesas_agregadas.csv")
        
        # Seleciona e normaliza colunas
        df_operadoras = df_agregado[['CNPJ', 'RazaoSocial', 'Modalidade', 'UF']].drop_duplicates('CNPJ')
        
        # A ordem do DF deve bater com a ordem das colunas passadas no COPY
        fast_copy_to_db(
            df_operadoras, 
            'operadoras', 
            engine, 
            columns=('cnpj', 'razao_social', 'modalidade', 'uf')
        )
        
        # 2. Carregar Despesas (Fato)
        logger.info("Lendo dados de despesas enriquecidas...")
        df_consol = pd.read_csv("data/enriched/consolidado_enriquecido.csv")
        
        # Filtra apenas o que vai para o banco (remove RazaoSocial que já está na dimensão)
        # Garante integridade referencial filtrando CNPJs que estão na dimensão operadoras
        cnpjs_validos = set(df_operadoras['CNPJ'])
        df_consol = df_consol[df_consol['CNPJ'].isin(cnpjs_validos)]
        
        df_fato = df_consol[['CNPJ', 'Ano', 'Trimestre', 'ValorDespesas']]
        
        fast_copy_to_db(
            df_fato, 
            'despesas_consolidadas', 
            engine, 
            columns=('cnpj', 'ano', 'trimestre', 'valor_despesa')
        )
        
        logger.info("Carga concluída com sucesso!")
        
    except Exception as e:
        logger.critical(f"Falha na execução: {e}")

