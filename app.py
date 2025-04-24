import streamlit as st
import time
from backend import cria_chain_conversa, folder_files

# Configurações de página
st.set_page_config(
    page_title="ChatPDF",
    page_icon="🤖",
    layout="centered"
)

def chat_window():
    st.markdown("## 🤖 Bem-vindo ao **Chat Senac PE**")
    st.markdown("## Assistente de ensino")
    st.markdown("## Redes de computadores e Cibersegurança")
    st.markdown("---")

    if 'chain' not in st.session_state:
        st.warning("📄 Clique em inicializar Chat.")
        st.stop()

    chain = st.session_state["chain"]
    memory = chain.memory
    mensagens = memory.load_memory_variables({})["chat_history"]

    with st.container():
        for mensagem in mensagens:
            with st.chat_message(mensagem.type):
                st.markdown(mensagem.content)

        nova_mensagem = st.chat_input("💬 Faça sua pergunta")
        if nova_mensagem:
            with st.chat_message("human"):
                st.markdown(nova_mensagem)
            with st.chat_message("ai"):
                st.markdown("⏳ Gerando resposta...")
            chain.invoke({"question": nova_mensagem})
            st.rerun()

def save_uploaded_files(uploaded_files, folder):
    """Salva arquivos enviados na pasta especificada."""
    for file in folder.glob("*.pdf"):
        file.unlink()
    for file in uploaded_files:
        (folder / file.name).write_bytes(file.read())

def main():
    with st.sidebar:
        # st.markdown("## 📂 Upload de PDFs")
        # uploaded_pdfs = st.file_uploader(
        #     "Adicione um ou mais arquivos PDF:",
        #     type="pdf",
        #     accept_multiple_files=True,
        #     help="Você pode adicionar vários arquivos ao mesmo tempo."
        # )

        # if uploaded_pdfs:
        #     save_uploaded_files(uploaded_pdfs, folder_files)
        #     st.success(f"✅ {len(uploaded_pdfs)} arquivo(s) salvo(s) com sucesso!")

        st.markdown("---")
        label_botao = "▶️ Inicializar Chatbot" if "chain" not in st.session_state else "🔄 Atualizar Chatbot"

        if st.button(label_botao, use_container_width=True):
            if len(list(folder_files.glob("*.pdf"))) == 0:
                st.error("⚠️ Adicione arquivos PDF antes de inicializar o chatbot.")
            else:
                st.info("🔧 Inicializando o Chatbot...")
                cria_chain_conversa()
                st.rerun()

    chat_window()

if __name__ == "__main__":
    main()
