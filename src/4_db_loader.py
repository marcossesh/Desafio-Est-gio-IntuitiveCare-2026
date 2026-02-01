import pandas as pd
from sqlalchemy import create_engine, text
import logging
import io
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/nome_banco")

def criar_schema(engine):
    logger.info("Criando schema do banco de dados (Loader)...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS despesas_consolidadas CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS operadoras CASCADE;"))
        
        conn.execute(text("""
            CREATE TABLE operadoras (
                registro_operadora VARCHAR(20),
                cnpj VARCHAR(14) PRIMARY KEY,
                razao_social VARCHAR(255),
                modalidade VARCHAR(100),
                uf CHAR(2)
            );
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS despesas_consolidadas (
                id SERIAL PRIMARY KEY,
                cnpj VARCHAR(14) REFERENCES operadoras(cnpj),
                ano INT,
                trimestre INT,
                valor_despesa DECIMAL(18,2)
            );
        """))

        conn.execute(text("TRUNCATE TABLE despesas_consolidadas, operadoras RESTART IDENTITY CASCADE;"))
        conn.commit()

def fast_copy_to_db(df, table_name, engine, columns=None):
    logger.info(f"Carregando {len(df)} linhas na tabela {table_name}...")
    
    output = io.StringIO()
    df.to_csv(output, index=False, header=False, sep='\t')
    output.seek(0)
    
    raw_conn = engine.raw_connection()
    cursor = raw_conn.cursor()
    try:
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
        
        logger.info("Lendo dados de operadoras...")
        # Lendo do consolidado enriquecido para garantir que temos todas as colunas
        df_completo = pd.read_csv("data/enriched/consolidado_enriquecido.csv")
        
        # Deduplicar para obter tabela de dimensão
        df_operadoras = df_completo[['REGISTRO_OPERADORA', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF']].drop_duplicates('CNPJ')
        
        # Assuming fast_copy_to_db is defined elsewhere
        fast_copy_to_db(
            df_operadoras, 
            'operadoras', 
            engine, 
            columns=('registro_operadora', 'cnpj', 'razao_social', 'modalidade', 'uf')
        )
        
        logger.info("Lendo dados de despesas enriquecidas (Fato)...")
        # df_completo já carregado
        
        df_fato = df_completo[['CNPJ', 'Ano', 'Trimestre', 'ValorDespesas']]
        
        # Assuming fast_copy_to_db is defined elsewhere
        fast_copy_to_db(
            df_fato, 
            'despesas_consolidadas', 
            engine, 
            columns=('cnpj', 'ano', 'trimestre', 'valor_despesa')
        )
        
        logger.info("Carga concluída com sucesso!")
        
    except Exception as e:
        logger.critical(f"Falha na execução: {e}")

