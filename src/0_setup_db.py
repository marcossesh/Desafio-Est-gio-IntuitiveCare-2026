import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

from sqlalchemy.engine.url import make_url

def create_database():
    """Conecta ao banco 'postgres' default e cria o banco alvo se não existir."""
    db_url_env = os.getenv("DATABASE_URL")
    if not db_url_env:
        logger.error("DATABASE_URL não definida no .env")
        return

    # Uso do make_url do SQLAlchemy para parsing robusto
    try:
        url = make_url(db_url_env)
        
        target_db_name = url.database
        if not target_db_name:
            target_db_name = "intuitive_care_db"

        logger.info(f"Tentando conectar em {url.host}:{url.port or 5432} com user '{url.username}'...")
        
        # Conecta ao banco administrativo 'postgres'
        con = psycopg2.connect(
            dbname='postgres',
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port or 5432
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Verifica existência
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{target_db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Banco '{target_db_name}' não encontrado. Criando...")
            cursor.execute(f"CREATE DATABASE {target_db_name}")
            logger.info(f"Banco '{target_db_name}' criado com sucesso!")
        else:
            logger.info(f"Banco '{target_db_name}' já existe.")
            
        cursor.close()
        con.close()
        
        return True

    except psycopg2.OperationalError as e:
        logger.error("ERRO DE CONEXÃO: Não foi possível conectar ao PostgreSQL.")
        logger.error(f"Detalhe: {e}")
        logger.warning("\nDICA: Verifique se a senha no arquivo '.env' está correta.")
        logger.warning(f"URL atual: {db_url_env}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    create_database()
