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
    """Lê o banco de dados (CSV) e analisa a frequência de palavras de TODO o histórico."""
    if not os.path.exists(ARQUIVO_HISTORICO):
        return []

    try:
        # Tenta ler o arquivo CSV gerado com ponto e vírgula
        df = pd.read_csv(ARQUIVO_HISTORICO, sep=';', encoding='utf-8')
        
        # Garante que a coluna 'Reclamacao' existe e não está vazia
        if df.empty or 'Reclamacao' not in df.columns:
            return []
        
        # Remove valores nulos e converte tudo para string
        textos = df['Reclamacao'].dropna().astype(str).tolist()
        
        if not textos:
            return []
            
        # Concatena todas as reclamações em um único texto global
        texto_completo = " ".join(textos)
        
    except Exception as e:
        st.error(f"Erro ao ler o banco de dados (CSV): {e}")
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
    """Salva a nova reclamação informada com data/hora no arquivo CSV garantindo a estrutura."""
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nova_linha = pd.DataFrame([{"Data_Hora": data_atual, "Reclamacao": texto}])
    
    if os.path.exists(ARQUIVO_HISTORICO):
        # Anexa sem repetir o cabeçalho
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False, sep=';', encoding='utf-8')
    else:
        # Cria o arquivo com cabeçalho se ele não existir
        nova_linha.to_csv(ARQUIVO_HISTORICO, mode='w', header=True, index=False, sep=';', encoding='utf-8')

# --- Interface Gráfica (Streamlit) ---

st.title("📊 Painel de Inteligência de Reclamações")
st.markdown("Ferramenta corporativa para consolidação de feedbacks e identificação de termos críticos extraídos diretamente da base de dados histórica.")
st.divider()

# Abas de Navegação da Aplicação
aba_analise, aba_historico = st.tabs(["🔍 Inserir & Análise Global", "📂 Banco de Dados (Histórico CSV)"])

with aba_analise:
    texto_informado = st.text_area(
        "Adicionar novo relatório de feedback / reclamação ao sistema:",
        placeholder="Cole o texto da nova reclamação aqui...",
        height=180,
        key="input_reclamacao"
    )

    col1, _ = st.columns([1, 4])

    with col1:
        botao_adicionar = st.button("Salvar no Banco & Atualizar", type="primary", use_container_width=True)

    if botao_adicionar:
        if not texto_informado.strip():
            st.warning("Por favor, insira um texto válido antes de salvar.")
        else:
            salvar_reclamacao_csv(texto_informado)
            st.success("Reclamação gravada com sucesso no banco de dados!")
            st.rerun() # Atualiza a tela imediatamente para refletir os novos dados na análise

    st.markdown("---")
    st.subheader("📈 Análise Estatística Consolidada (Base Completa)")
    st.markdown("Resultados calculados utilizando **absolutamente todos os registros** acumulados no arquivo CSV.")

    # Executa a análise baseada no corpus completo
    resultados = analisar_frequencia_corpus(limite=15)

    if resultados:
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
        st.info("O banco de dados ainda está vazio ou não contém palavras válidas suficientes. Adicione registros na aba acima.")

with aba_historico:
    st.subheader("Registros Armazenados no Servidor")
    
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            df_historico = pd.read_csv(ARQUIVO_HISTORICO, sep=';', encoding='utf-8')
            st.metric("Total de Registros na Base", len(df_historico))
            st.dataframe(df_historico, use_container_width=True, hide_index=True)
            
            historico_csv = df_historico.to_csv(index=False, sep=';').encode('utf-8')
            st.download_button(
                label="📥 Baixar Base Completa de Reclamações (CSV)",
                data=historico_csv,
                file_name="historico_reclamacoes_geral.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f'Erro ao carregar a tabela de histórico: {e}')
    else:
        st.warning("O arquivo `historico_reclamacoes.csv` ainda não foi criado no servidor.")

# Rodapé
st.markdown("---")
st.caption("Governança e Qualidade de Produto &copy; 2026")