import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_step(script_name):
    logger.info(f"Iniciando etapa: {script_name}")
    # Usamos sys.executable para garantir que use o mesmo venv
    result = subprocess.run([sys.executable, script_path(script_name)], capture_output=False)
    
    if result.returncode != 0:
        logger.error(f"Erro na etapa {script_name}. Abortando pipeline.")
        sys.exit(1)

def script_path(name):

    # Ajuste conforme a localização dos seus scripts
    if name.startswith("test"):
        return os.path.join("tests", name)
    return os.path.join("src", name)

if __name__ == "__main__":
    logger.info("=== INICIANDO PIPELINE DE DADOS INTUITIVE CARE 2026 ===")

    logger.info("Rodando testes unitários...")
    test_result = subprocess.run(["pytest", "tests/test_pipeline.py"], capture_output=False)
    if test_result.returncode != 0:
        logger.error("Testes falharam. Corrija o código antes de prosseguir.")
        sys.exit(1)

    # 2. Pipeline de ETL
    pipeline = [
        "1_scraper.py",    # Extração
        "2_processor.py",  # Consolidação
        "3_enricher.py",   # Validação e Agregação
        "0_setup_db.py",   # Preparação do Banco (Docker)
        "4_db_loader.py"   # Carga SQL
    ]

    for script in pipeline:
        run_step(script)

    logger.info("PIPELINE FINALIZADO COM SUCESSO!")
    logger.info("Os dados estão prontos no banco e os CSVs na pasta data/")
