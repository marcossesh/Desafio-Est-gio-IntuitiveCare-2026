import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "postgresql://usuario:senha@localhost:5432/nome_banco")

engine = create_engine(DB_URL)
with engine.connect() as conn:
    targets = [
        "FCA SAÚDE", "BRADESCO SAÚDE"
    ]
    
    print("--- Identificação ---")
    cnpjs = []
    for name in targets:
        query = text("SELECT registro_operadora, cnpj, razao_social FROM operadoras WHERE razao_social ILIKE :name")
        rows = conn.execute(query, {"name": f"%{name}%"}).fetchall()
        for row in rows:
            print(row)
            cnpjs.append(row[1])

    print("\n--- Dados no Banco ---")
    if cnpjs:
        if len(cnpjs) == 1:
            in_clause = f"('{cnpjs[0]}')"
        else:
            in_clause = str(tuple(cnpjs))
            
        query_desp = text(f"SELECT * FROM despesas_consolidadas WHERE cnpj IN {in_clause} ORDER BY cnpj, ano, trimestre")
        rows_desp = conn.execute(query_desp).fetchall()
        for row in rows_desp:
            print(row)
