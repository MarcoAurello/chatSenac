from pathlib import Path
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_openai.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import random
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# 🔐 Carrega variáveis de ambiente
_ = load_dotenv(find_dotenv())

# 📁 Diretório onde os PDFs serão armazenados
folder_files = Path(__file__).parent / "files"
model_name = "gpt-3.5-turbo-0125"
DEBUG = False  # Ativa logs no console do Streamlit para debug

# 📄 Carrega todos os documentos PDF da pasta
def importar_documentos() -> list:
    documentos = []
    for arquivo in folder_files.glob("*.pdf"):
        if DEBUG: st.write(f"🔍 Carregando {arquivo.name}")
        loader = PyPDFLoader(arquivo)
        documentos_arquivo = loader.load()
        documentos.extend(documentos_arquivo)
    return documentos

# ✂️ Divide documentos em pedaços menores com sobreposição
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

# 🧠 Cria um banco vetorial FAISS com embeddings OpenAI
def criar_vector_store(documentos):
    embedding_model = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(
        documents=documentos,
        embedding=embedding_model
    )
    return vector_store

# 🎯 Gera perguntas de quiz com variação aleatória
def gerar_perguntas_quiz(documentos, qtd_perguntas=5):
    chat = ChatOpenAI(model=model_name)

    random.shuffle(documentos)
    trechos_selecionados = documentos[:min(5, len(documentos))]
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

# 🤖 Cria a cadeia de conversa com memória e busca semântica
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

    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        memory=memory,
        retriever=retriever,
        return_source_documents=True,
        verbose=DEBUG
    )

    st.session_state["chain"] = chain
    return chain
