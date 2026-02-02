import logging
import os
import zipfile

def setup_logger(name, log_file="data/pipeline.log"):
    """
    Configures and returns a logger instance.
    Ensures the data directory exists.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if logger is already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File Handler
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Stream Handler (Console)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def zip_file(source_path, dest_zip_path):
    """
    Compresses a single file into a ZIP archive.
    """
    logger = logging.getLogger("utils.zip_file")
    logger.info(f"Compactando arquivo para: {dest_zip_path}")
    
    try:
        os.makedirs(os.path.dirname(dest_zip_path), exist_ok=True)
        with zipfile.ZipFile(dest_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(source_path, arcname=os.path.basename(source_path))
    except Exception as e:
        logger.error(f"Erro ao zipar {source_path}: {e}")
        raise
