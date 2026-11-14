import streamlit as st
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import pandas as pd
from datetime import datetime
import os

# Configuração da página
st.set_page_config(
    page_title="Painel de Inteligência de Reclamações",
    page_icon="📊",
    layout="wide"
)

# Caminho do arquivo CSV de histórico
ARQUIVO_HISTORICO = "historico_reclamacoes.csv"

# Garante que os recursos necessários do NLTK estejam baixados
@st.cache_resource
def carregar_nltk():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

carregar_nltk()

def analisar_frequencia(texto, limite=15):
    if not texto or not texto.strip():
        return []

    # Normalização: converter para minúsculas
    texto_limpo = texto.lower()

    # Tokenização das palavras
    tokens = word_tokenize(texto_limpo, language='portuguese')

    # Obter lista de stop words e pontuações em português
    stop_words = set(stopwords.words('portuguese'))
    pontuacoes = set(string.punctuation)
    extras = {'vc', 'q', 'pra', 'pro', 'tô', 'né', 'também', 'ter', 'ser'}
    stop_words.update(extras)

    # Filtrar tokens
    palavras_filtradas = [
        palavra for palavra in tokens 
        if palavra not in stop_words 
        and palavra not in pontuacoes 
        and len(palavra) > 2 
        and palavra.isalpha()
    ]

    # Contagem de frequência
    frequencia = nltk.FreqDist(palavras_filtradas)
    
    return frequencia.most_common(limite)

def salvar_reclamacao_csv(texto):
    """Salva a reclamação informada com data/hora no arquivo CSV."""
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nova_linha = pd.DataFrame([{"Data_Hora": data_atual, "Reclamacao": texto}])
    
    if os.path.exists(ARQUIVO_HISTORICO):
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False, sep=';', encoding='utf-8')
    else:
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='w', header=True, index=False, sep=';', encoding='utf-8')

# --- Interface Gráfica (Streamlit) ---

st.title("📊 Painel de Inteligência de Reclamações")
st.markdown("Ferramenta corporativa para identificar termos críticos e armazenar feedbacks de clientes para melhoria contínua de produtos.")
st.divider()

# Abas de Navegação da Aplicação
aba_analise, aba_historico = st.tabs(["🔍 Nova Análise", "📂 Histórico de Reclamações Gravadas"])

with aba_analise:
    # Campo de entrada de texto
    texto_informado = st.text_area(
        "Insira abaixo o relatório de feedback ou texto consolidado de reclamação:",
        placeholder="Cole o texto das reclamações dos clientes aqui...",
        height=200,
        key="input_reclamacao"
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        botao_analisar = st.button("Analisar & Gravar", type="primary", use_container_width=True)

    if botao_analisar:
        if not texto_informado.strip():
            st.warning("Por favor, insira um texto válido para análise.")
        else:
            with st.spinner("Processando texto, salvando no CSV e calculando frequências..."):
                # Grava a reclamação no CSV institucional
                salvar_reclamacao_csv(texto_informado)
                
                # Realiza a análise NLP
                resultados = analisar_frequencia(texto_informado, limite=15)

            if resultados:
                st.success("Reclamação gravada com sucesso no histórico e análise concluída!")
                
                # Convertendo resultados para DataFrame do pandas
                df_resultados = pd.DataFrame(resultados, columns=["Palavra", "Ocorrências"])
                df_resultados["Palavra"] = df_resultados["Palavra"].str.capitalize()
                
                # Sub-abas para Gráfico e Tabela da análise atual
                sub_tab_grafico, sub_tab_tabela = st.tabs(["📈 Gráfico da Análise", "📋 Tabela de Frequência"])
                
                with sub_tab_grafico:
                    st.subheader("Termos Mais Recorrentes")
                    chart_data = df_resultados.set_index("Palavra")
                    st.bar_chart(chart_data)
                
                with sub_tab_tabela:
                    st.subheader("Ocorrências Identificadas")
                    st.dataframe(df_resultados, use_container_width=True, hide_index=True)

                # Botão de Exportação da Análise Atual
                csv_data = df_resultados.to_csv(index=False, sep=';').encode('utf-8')
                st.download_button(
                    label="📥 Baixar Resultado da Análise (CSV)",
                    data=csv_data,
                    file_name="analise_frequencia_atual.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Reclamação gravada, mas nenhum termo relevante foi encontrado após a filtragem.")

with aba_historico:
    st.subheader("Base de Dados de Reclamações Registradas")
    st.markdown("Visualização de todas as entradas submetidas pelos colaboradores e armazenadas no servidor.")
    
    if os.path.exists(ARQUIVO_HISTORICO):
        df_historico = pd.read_csv(ARQUIVO_HISTORICO, sep=';')
        
        st.metric("Total de Reclamações Registradas", len(df_historico))
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
        
        # Botão para baixar todo o histórico consolidado
        historico_csv = df_historico.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="📥 Baixar Histórico Completo de Reclamações (CSV)",
            data=historico_csv,
            file_name="historico_reclamacoes_geral.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhuma reclamação foi gravada no arquivo CSV ainda. Realize uma análise na aba anterior.")

# Rodapé
st.markdown("---")
st.caption("Governança e Qualidade de Produto &copy; 2026")