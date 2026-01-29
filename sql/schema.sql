CREATE TABLE operadoras (
    cnpj VARCHAR(14) PRIMARY KEY,
    razao_social VARCHAR(255),
    modalidade VARCHAR(100),
    uf CHAR(2)
);


CREATE TABLE despesas_historicas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) REFERENCES operadoras(cnpj),
    ano INT,
    trimestre INT,
    valor_despesa DECIMAL(18,2)
);

CREATE TABLE despesas_estatisticas (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) REFERENCES operadoras(cnpj),
    total_despesas DECIMAL(18,2),
    media_trimestral DECIMAL(18,2),
    desvio_padrao DECIMAL(18,2)
);

-- Top 10 operadoras com maiores despesas no período mais recente disponível.
SELECT 
    o.razao_social,
    dh.valor_despesa,
    dh.ano,
    dh.trimestre
FROM 
    operadoras o
JOIN 
    despesas_historicas dh ON o.cnpj = dh.cnpj
WHERE 
    (dh.ano, dh.trimestre) = (
        SELECT ano, trimestre 
        FROM despesas_historicas 
        ORDER BY ano DESC, trimestre DESC 
        LIMIT 1
    )
ORDER BY 
    dh.valor_despesa DESC
LIMIT 10;
    
-- Média de despesa por modalidade de operadora.
SELECT 
    operadoras.modalidade,
    AVG(despesas_historicas.valor_despesa) AS media_despesa
FROM 
    operadoras
JOIN 
    despesas_historicas ON operadoras.cnpj = despesas_historicas.cnpj
GROUP BY 
    operadoras.modalidade;

-- Operadoras que apresentaram a maior variação (desvio padrão) de despesas.
SELECT 
    operadoras.razao_social,
    despesas_estatisticas.desvio_padrao
FROM 
    operadoras
JOIN 
    despesas_estatisticas ON operadoras.cnpj = despesas_estatisticas.cnpj
ORDER BY 
    despesas_estatisticas.desvio_padrao DESC
LIMIT 10;
