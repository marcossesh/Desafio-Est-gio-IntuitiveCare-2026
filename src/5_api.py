from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()


app = FastAPI(title="Intuitive Care API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada. Verifique o arquivo .env.")

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OperadoraResponse(BaseModel):
    cnpj: str
    razao_social: str
    modalidade: str
    uf: str

class PaginatedResponse(BaseModel):
    data: List[OperadoraResponse]
    total: int
    page: int
    limit: int



# Rota para lista de operadoras com paginação
@app.get("/api/operadoras", response_model=PaginatedResponse)
def list_operadoras(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    offset = (page - 1) * limit
    
    query = db.execute(text("SELECT cnpj, razao_social, modalidade, uf FROM operadoras"))
    all_data = query.fetchall()
    
    total = len(all_data)
    data = all_data[offset : offset + limit]
    
    result = [dict(row._mapping) for row in data]
    
    return {
        "data": result,
        "total": total,
        "page": page,
        "limit": limit
    }

# Rota para detalhes de uma operadora específica
@app.get("/api/operadoras/{cnpj}")
def get_operadora(cnpj: str, db: Session = Depends(get_db)):
    query = db.execute(
        text("SELECT cnpj, razao_social, modalidade, uf FROM operadoras WHERE cnpj = :cnpj"),
        {"cnpj": cnpj}
    )
    row = query.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return dict(row._mapping)

# Rota para histórico de despesas
@app.get("/api/operadoras/{cnpj}/despesas")
def get_operadora_despesas(cnpj: str, db: Session = Depends(get_db)):
    query = db.execute(
        text("""
            SELECT ano, trimestre, valor_despesa 
            FROM despesas_consolidadas 
            WHERE cnpj = :cnpj 
            ORDER BY ano DESC, trimestre DESC
        """),
        {"cnpj": cnpj}
    )
    return [dict(row._mapping) for row in query.fetchall()]

# Rota de Estatísticas Globais
@app.get("/api/estatisticas")
def get_global_stats(db: Session = Depends(get_db)):
    # Total e Média
    stats_query = db.execute(text("""
        SELECT 
            SUM(valor_despesa) as total_geral,
            AVG(valor_despesa) as media_geral
        FROM despesas_consolidadas
    """))
    stats = stats_query.fetchone()._mapping

    # Top 5 Operadoras
    top5_query = db.execute(text("""
        SELECT o.razao_social, SUM(d.valor_despesa) as total
        FROM despesas_consolidadas d
        JOIN operadoras o ON d.cnpj = o.cnpj
        GROUP BY o.razao_social
        ORDER BY total DESC
        LIMIT 5
    """))
    top5 = [dict(row._mapping) for row in top5_query.fetchall()]

    return {
        "total_despesas": stats["total_geral"],
        "media_despesas": stats["media_geral"],
        "top_5_operadoras": top5
    }