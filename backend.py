from pathlib import Path
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_openai.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory

import streamlit as st
from dotenv import load_dotenv, find_dotenv

# 🔐 Carrega variáveis de ambiente
_ = load_dotenv(find_dotenv())

# 📁 Diretório onde os PDFs serão armazenados
folder_files = Path(__file__).parent / "files"
model_name = "gpt-3.5-turbo-0125"

# Ativar logs no console Streamlit (para debug)
DEBUG = False

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
def criar_vector_store(documentos):  # <-- aqui o nome está correto
    embedding_model = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(
        documents=documentos,  # <-- aqui estava "documents", mudei para "documentos"
        embedding=embedding_model
    )
    return vector_store

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
