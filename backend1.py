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
    session_id = st.session_state.get("session_id", "")

    for arquivo in folder_files.glob(f"*_{session_id}.pdf"):
        loader = PyPDFLoader(str(arquivo))
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
    if not documentos:
        st.error("❌ Nenhum documento foi fornecido para criar o vetor store.")
        return None

    # Verificação opcional: garantir que todos os documentos têm conteúdo textual
    for i, doc in enumerate(documentos):
        if not hasattr(doc, 'page_content') and not hasattr(doc, 'text'):
            st.error(f"❌ Documento na posição {i} não possui texto válido.")
            return None

    embedding_model = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

    # Criação segura do vector store
    try:
        vector_store = FAISS.from_documents(
            documents=documentos,
            embedding=embedding_model
        )
    except IndexError as e:
        st.error("❌ Erro ao criar o índice FAISS. Verifique se os documentos têm conteúdo válido.")
        return None

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
Você é um professor dedicado que busca não apenas transmitir conhecimento, mas também provocar reflexões e incentivar a construção do saber junto ao aluno.
Adapte sua linguagem conforme o nível de entendimento demonstrado pelo aluno. Use exemplos simples, analogias do cotidiano e perguntas para manter o aluno engajado e garantir compreensão.

Use o seguinte conteúdo dos documentos para responder:
{context}

Baseado nisso, e no histórico da conversa:
{chat_history}

E na nova pergunta:
{question}

Se o aluno demonstrar dúvidas ou dificuldades, revisite os conceitos básicos de forma acessível.
Responda de forma didática, amigável e envolvente. Seu objetivo é não só responder, mas ajudar o aluno a aprender de verdade.
"""

    if fazer_reflexao:
        base_prompt += """
Após sua explicação, estimule a reflexão do aluno com uma pergunta aberta como:
- "O que você acha sobre isso?"
- "Por que você acredita que isso acontece?"
- "Você conseguiria pensar em um exemplo onde isso se aplica?"
- "Você já viveu algo parecido com isso?"
- "Consegue pensar em como isso se relaciona com o seu dia a dia?"
- "Qual parte te chamou mais atenção? Por quê?"
"""
        st.session_state.interacoes_sem_reflexao = 0
    else:
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

    if not documentos:
        st.session_state.erro_chat = "❌ Nenhum arquivo encontrado para inicializar o chat. Por favor, carregue um arquivo PDF."
        return None

    documentos = dividir_documentos(documentos)
    vector_store = criar_vector_store(documentos)

    if vector_store is None:
        st.session_state.erro_chat = "❌ Não foi possível criar o vector store. Verifique os documentos."
        return None

    chat_model = ChatOpenAI(model=model_name)

    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key="chat_history",
        output_key="answer"
    )

    try:
        retriever = vector_store.as_retriever()
    except AttributeError:
        st.session_state.erro_chat = "❌ O vector store não possui o método 'as_retriever'. Verifique a criação do vector store."
        return None

    # Limpa mensagens de erro anteriores, se houve sucesso até aqui
    st.session_state.pop("erro_chat", None)

    # Inicializa contadores de interação
    if "num_interacoes" not in st.session_state:
        st.session_state.num_interacoes = 0
    if "interacoes_sem_reflexao" not in st.session_state:
        st.session_state.interacoes_sem_reflexao = 0

    # Gera o prompt dinâmico inicial
    prompt_template = gerar_prompt_dinamico()

    # Cria o chain com prompt personalizado
    chain = ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        memory=memory,
        retriever=retriever,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt_template},
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
