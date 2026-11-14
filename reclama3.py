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

def analisar_frequencia_corpus(limite=15):
    """Analisa a frequência de palavras utilizando TODAS as reclamações salvas no CSV."""
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []

    try:
        df = pd.read_csv(ARQUIVO_HISTORICO, sep=';')
        if df.empty or 'Reclamacao' not in df.columns:
            return []
        
        # Concatena todos os textos de reclamação salvos em uma única string gigante
        texto_completo = " ".join(df['Reclamacao'].astype(str).tolist())
    except Exception:
        return []

    if not texto_completo.strip():
        return []

    # Normalização: converter para minúsculas
    texto_limpo = texto_completo.lower()

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

    # Contagem de frequência global
    frequencia = nltk.FreqDist(palavras_filtradas)
    
    return frequencia.most_common(limite)

def salvar_reclamacao_csv(texto):
    """Salva a nova reclamação informada com data/hora no arquivo CSV."""
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nova_linha = pd.DataFrame([{"Data_Hora": data_atual, "Reclamacao": texto}])
    
    if os.path.exists(ARQUIVO_HISTORICO):
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False, sep=';', encoding='utf-8')
    else:
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='w', header=True, index=False, sep=';', encoding='utf-8')

# --- Interface Gráfica (Streamlit) ---

st.title("📊 Painel de Inteligência de Reclamações")
st.markdown("Ferramenta corporativa para consolidação de feedbacks e identificação de termos críticos em **todo o histórico acumulado**.")
st.divider()

# Abas de Navegação da Aplicação
aba_analise, aba_historico = st.tabs(["🔍 Inserir & Analisar Base Completa", "📂 Histórico de Reclamações Gravadas"])

with aba_analise:
    # Campo de entrada de texto
    texto_informado = st.text_area(
        "Adicionar novo relatório de feedback / reclamação ao sistema:",
        placeholder="Cole o texto da nova reclamação aqui...",
        height=180,
        key="input_reclamacao"
    )

    col1, _ = st.columns([1, 4])

    with col1:
        botao_adicionar = st.button("Salvar & Atualizar Análise", type="primary", use_container_width=True)

    if botao_adicionar:
        if not texto_informado.strip():
            st.warning("Por favor, insira um texto válido antes de salvar.")
        else:
            salvar_reclamacao_csv(texto_informado)
            st.success("Nova reclamação anexada com sucesso à base de dados global!")

    st.markdown("---")
    st.subheader("📈 Análise Consolidada de Frequência (Todos os Dados)")
    st.markdown("Abaixo estão os termos mais recorrentes considerando **todas as reclamações já gravadas** no servidor.")

    # Executa a análise baseada estritamente no corpus completo do CSV
    resultados = analisar_frequencia_corpus(limite=15)

    if resultados:
        # Convertendo resultados globais para DataFrame do pandas
        df_resultados = pd.DataFrame(resultados, columns=["Palavra", "Ocorrências"])
        df_resultados["Palavra"] = df_resultados["Palavra"].str.capitalize()
        
        sub_tab_grafico, sub_tab_tabela = st.tabs(["📊 Gráfico Consolidado", "📋 Tabela Detalhada"])
        
        with sub_tab_grafico:
            chart_data = df_resultados.set_index("Palavra")
            st.bar_chart(chart_data)
        
        with sub_tab_tabela:
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)

        # Botão de Exportação da Análise Consolidada
        csv_data = df_resultados.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="📥 Baixar Relatório Consolidado (CSV)",
            data=csv_data,
            file_name="relatorio_frequencia_consolidado.csv",
            mime="text/csv"
        )
    else:
        st.info("Ainda não há dados suficientes no histórico para gerar a análise estatística. Adicione a primeira reclamação acima.")

with aba_historico:
    st.subheader("Repositório de Reclamações Registradas")
    st.markdown("Listagem completa de todas as entradas submetidas e armazenadas no arquivo corporativo.")
    
    if os.path.exists(ARQUIVO_HISTORICO):
        df_historico = pd.read_csv(ARQUIVO_HISTORICO, sep=';')
        
        st.metric("Total de Registros na Base", len(df_historico))
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
        st.info("O arquivo de histórico ainda não foi criado.")

# Rodapé
st.markdown("---")
st.caption("Governança e Qualidade de Produto &copy; 2026")