import pytest
import pandas as pd
import sys
import os
import importlib.util

# Helper function to import modules with names starting with numbers
def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Load modules dynamically
# Precisamos do caminho absoluto ou relativo correto. 
# Considerando que vamos rodar pytest da raiz.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
processor_path = os.path.join(BASE_DIR, "src", "2_processor.py")
enricher_path = os.path.join(BASE_DIR, "src", "3_enricher.py")

processor = import_module_from_path("src_2_processor", processor_path)
enricher = import_module_from_path("src_3_enricher", enricher_path)

extrair_metadados = processor.extrair_metadados
validar_e_corrigir = enricher.validar_e_corrigir

def test_extrair_metadados_sucesso():
    """Testa se o Regex identifica corretamente Ano e Trimestre no nome do arquivo."""
    nome = "3T2025_demonstracoes.csv"
    ano, trimestre = extrair_metadados(nome)
    assert ano == "2025"
    assert trimestre == "3"

def test_extrair_metadados_fallback():
    """Testa se o fallback funciona para nomes fora do padrão."""
    nome = "arquivo_generico.csv"
    ano, trimestre = extrair_metadados(nome)
    assert ano == "2025"  # Seu valor default
    assert trimestre == "1"

def test_validacao_cnpj_invalido():
    """Testa se o enriquecedor descarta CNPJs matematicamente inválidos."""
    # Criamos um mini-dataframe de teste
    df_teste = pd.DataFrame({
        'CNPJ': ['00000000000000', '123'], # CNPJs óbvios e inválidos
        'RazaoSocial': ['Teste', 'Teste 2'],
        'ValorDespesas': [100, 200],
        'Ano': [2025, 2025],
        'Trimestre': [1, 1]
    })
    
    # Mock do cadastro vazio para não falhar no merge
    df_cadastral = pd.DataFrame(columns=['REGISTRO_OPERADORA', 'CNPJ', 'Razao_Social', 'UF', 'Modalidade'])
    
    # A função deve retornar um DF vazio pois não há CNPJs válidos
    df_resultado = validar_e_corrigir(df_teste, df_cadastral)
    assert len(df_resultado) == 0

def test_filtro_despesas_negativas():
    """Testa se o pipeline remove valores negativos (regra de negócio)."""
    df_teste = pd.DataFrame({
        'CNPJ': ['62638374000194'], # CNPJ real do Trasmontano
        'RazaoSocial': ['Teste'],
        'ValorDespesas': [-500.0],
        'Ano': [2025],
        'Trimestre': [1]
    })
    df_cadastral = pd.DataFrame({
        'REGISTRO_OPERADORA': [123],
        'CNPJ': ['62638374000194'],
        'Razao_Social': ['Teste Real'],
        'UF': ['SP'],
        'Modalidade': ['Medicina de Grupo']
    })
    
    df_resultado = validar_e_corrigir(df_teste, df_cadastral)
    assert len(df_resultado) == 0 # Deve ser filtrado por ser negativo
