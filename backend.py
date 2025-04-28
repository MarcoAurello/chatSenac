from pathlib import Path
import random
import os

import streamlit as st
from dotenv import load_dotenv, find_dotenv

from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain

# 🔐 Carrega variáveis de ambiente
_ = load_dotenv(find_dotenv())

# 📁 Diretório onde os PDFs serão armazenados
folder_files = Path(__file__).parent / "files"
model_name = "gpt-3.5-turbo-0125"
DEBUG = False  # Ativa logs no console do Streamlit para debug

# 📄 Função para importar documentos
def importar_documentos() -> list:
    documentos = []
    for arquivo in folder_files.glob("*.pdf"):
        if DEBUG: st.write(f"🔍 Carregando {arquivo.name}")
        loader = PyPDFLoader(arquivo)
        documentos.extend(loader.load())
    return documentos

# ✂️ Função para dividir documentos
def dividir_documentos(documentos: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    documentos_divididos = splitter.split_documents(documentos)

    for i, doc in enumerate(documentos_divididos):
        doc.metadata["source"] = Path(doc.metadata.get("source", "Desconhecido")).name
        doc.metadata["doc_id"] = i

    return documentos_divididos

# 🧠 Cria o vector store (FAISS)
def criar_vector_store(documentos):
    embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    vector_store = FAISS.from_documents(
        documents=documentos,
        embedding=embedding_model
    )
    return vector_store

# 🎯 Gera perguntas de quiz (não alterado)
def gerar_perguntas_quiz(documentos, qtd_perguntas=10):
    chat = ChatOpenAI(model=model_name)
    random.shuffle(documentos)
    trechos_selecionados = documentos[:min(qtd_perguntas, len(documentos))]
    texto_base = "\n".join([doc.page_content for doc in trechos_selecionados])

    prompt = f"""
    A partir do texto abaixo, gere {qtd_perguntas} perguntas de múltipla escolha com 4 alternativas cada.

    Para cada pergunta, siga este formato:
    Pergunta: [texto da pergunta]
    A) [opção 1]
    B) [opção 2]
    C) [opção 3]
    D) [opção 4]
    Resposta: [letra da opção correta]
    Explicação: [breve explicação de por que essa é a resposta correta]

    Texto base:
    {texto_base}
    """

    resposta = chat.invoke(prompt)
    return resposta.content

# 🔥 Função para gerar o prompt dinamicamente
def gerar_prompt_dinamico():
    # 30% de chance de fazer uma pergunta reflexiva
    fazer_reflexao = random.random() < 0.3

    # Forçar reflexão após 3 interações sem reflexão
    if st.session_state.interacoes_sem_reflexao >= 3:
        fazer_reflexao = True

    base_prompt = """
Você é um tutor paciente conversando com um aluno.

Use o seguinte conteúdo dos documentos para responder:
{context}

Baseado nisso, e no histórico de conversa:
{chat_history}

E na nova pergunta:
{question}

Responda de maneira clara, didática e amigável.
"""

    if fazer_reflexao:
        base_prompt += """
Depois de responder, estimule o aluno a refletir com uma pergunta aberta como:
- "O que você acha sobre isso?"
- "Por que você acredita que isso acontece?"
- "Você conseguiria pensar em um exemplo onde isso se aplica?"
"""
        # Resetar contador
        st.session_state.interacoes_sem_reflexao = 0
    else:
        # Aumenta contador
        st.session_state.interacoes_sem_reflexao += 1

    base_prompt += """
Agora responda:
"""

    return PromptTemplate(
        input_variables=["chat_history", "question", "context"],
        template=base_prompt
    )

# 🚀 Função principal para criar o chain
def cria_chain_conversa():
    documentos = importar_documentos()
    documentos = dividir_documentos(documentos)
    vector_store = criar_vector_store(documentos)

    chat_model = ChatOpenAI(model=model_name)

    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )

    retriever = vector_store.as_retriever()

    # Inicializa contadores de interação
    if "num_interacoes" not in st.session_state:
        st.session_state.num_interacoes = 0
    if "interacoes_sem_reflexao" not in st.session_state:
        st.session_state.interacoes_sem_reflexao = 0

    # Cria o chain (sem prompt fixo ainda)
    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        memory=memory,
        retriever=retriever,
        return_source_documents=True,
        verbose=DEBUG
    )

    st.session_state["chain"] = chain

    return chain

# 🗨️ Função para interagir com o usuário (com atualização dinâmica do prompt)
def responder_usuario(pergunta_usuario):
    # Gera novo prompt dinâmico a cada interação
    prompt_template = gerar_prompt_dinamico()

    # Atualiza o prompt do chain em runtime
    st.session_state["chain"].combine_docs_chain.llm_chain.prompt = prompt_template

    resposta = st.session_state["chain"].invoke({"question": pergunta_usuario})

    # Atualiza contador total de interações
    st.session_state.num_interacoes += 1

    return resposta["answer"]
