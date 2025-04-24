import streamlit as st
import time
from backend import cria_chain_conversa, folder_files
from pathlib import Path

# Configurações de página
st.set_page_config(
    page_title="ChatPDF",
    page_icon="🤖",
    layout="centered"
)

def chat_window():
    st.markdown("## 🤖 **Assistente de ensino Senac PE**")
    st.markdown("##  **Envie um Pdf**")
    st.markdown(" **Tire duvidas no chat**")
    st.markdown(" **Estude com o quiz**")
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

def display_existing_files(folder):
    # Listar os arquivos presentes no diretório
    arquivos = list(folder.glob("*.pdf"))
    if arquivos:
        st.markdown("### Arquivos já enviados:")
        for arquivo in arquivos:
            col1, col2 = st.columns([4, 1])  # Criar duas colunas, uma para o nome e outra para o botão
            with col1:
                st.markdown(f"- {arquivo.name}")
            with col2:
                # Adiciona um botão de exclusão ao lado do arquivo
                if st.button(f"❌", key=arquivo.name):
                    excluir_arquivo(arquivo)
                    st.rerun()  # Atualiza a página após a exclusão
    else:
        st.warning("⚠️ Nenhum arquivo PDF encontrado.")

# Função para excluir o arquivo
def excluir_arquivo(arquivo):
    try:
        arquivo.unlink()  # Exclui o arquivo da pasta
        st.success(f"✅ Arquivo {arquivo.name} excluído com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao excluir o arquivo {arquivo.name}: {str(e)}")

def quiz_window(perguntas_raw):
    st.markdown("## 🧠 Quiz baseado nos PDFs enviados")

    if "acertos" not in st.session_state:
        st.session_state["acertos"] = 0

    perguntas_brutas = perguntas_raw.strip().split("\n\nPergunta:")
    if perguntas_brutas[0].startswith("Pergunta:"):
        perguntas_brutas[0] = perguntas_brutas[0][len("Pergunta:"):]

    for idx, pergunta_raw in enumerate(perguntas_brutas):
        linhas = pergunta_raw.strip().split("\n")

        if len(linhas) < 7:
            st.warning(f"⚠️ Pergunta {idx + 1} mal formatada ou incompleta. Pulando...")
            continue

        pergunta_texto = linhas[0]
        opcoes = linhas[1:5]
        resposta_certa = linhas[5].split(":")[-1].strip().upper()[0]  # <-- alteração aqui

        explicacao = linhas[6].split(":", 1)[-1].strip()

        st.markdown(f"**Pergunta {idx + 1}:** {pergunta_texto}")
        escolha = st.radio("Escolha uma opção:", opcoes, key=f"resposta_{idx}")

        letra_escolhida = escolha[0].upper()
        correta = (letra_escolhida == resposta_certa)

        if f"resposta_mostrada_{idx}" not in st.session_state:
            st.session_state[f"resposta_mostrada_{idx}"] = False

        if st.button(f"Ver resposta da Pergunta {idx + 1}", key=f"ver_resposta_{idx}"):
            st.session_state[f"resposta_mostrada_{idx}"] = True
            if correta:
                st.session_state["acertos"] += 1

        if st.session_state[f"resposta_mostrada_{idx}"]:
            index_resposta_certa = ord(resposta_certa) - ord("A")
            if 0 <= index_resposta_certa < len(opcoes):
                texto_resposta = opcoes[index_resposta_certa][3:].strip()
            else:
                texto_resposta = "opção desconhecida"

            if correta:
                st.success(f"✅ Resposta correta! {resposta_certa}) {texto_resposta}")
            else:
                st.error(f"❌ Resposta incorreta. A correta é **{resposta_certa}**) {texto_resposta}")
            st.markdown(f"🧠 **Explicação:** {explicacao}")
            st.markdown("________________________________")

    if st.button("🔁 Refazer Quiz com PDFs", use_container_width=True, key="botao_quiz_refazer"):
        st.session_state.pop("quiz", None)
        from backend import importar_documentos, dividir_documentos, gerar_perguntas_quiz
        documentos = importar_documentos()
        documentos = dividir_documentos(documentos)
        st.session_state["quiz"] = gerar_perguntas_quiz(documentos)
        st.session_state["acertos"] = 0
        st.rerun()

    st.markdown(f"### 🎯 Total de acertos: {st.session_state['acertos']} de {len(perguntas_brutas)} perguntas.")


def save_uploaded_files(uploaded_files, folder):
    for file in folder.glob("*.pdf"):
        file.unlink()
    for file in uploaded_files:
        (folder / file.name).write_bytes(file.read())

def main():
    with st.sidebar:
        st.markdown("## 📂 Upload de PDFs")
        display_existing_files(folder_files)
        uploaded_pdfs = st.file_uploader(
            "Adicione um ou mais arquivos PDF:",
            type="pdf",
            accept_multiple_files=True,
            help="Você pode adicionar vários arquivos ao mesmo tempo."
        )

        if uploaded_pdfs:
            save_uploaded_files(uploaded_pdfs, folder_files)
            st.success(f"✅ {len(uploaded_pdfs)} arquivo(s) salvo(s) com sucesso!")

        st.markdown("---")
        label_botao = "▶️ Inicializar Chatbot" if "chain" not in st.session_state else "🔄 Atualizar Chatbot"

        if st.button(label_botao, use_container_width=True, key="botao_inicializar"):
            if len(list(folder_files.glob("*.pdf"))) == 0:
                st.error("⚠️ Adicione arquivos PDF antes de inicializar o chatbot.")
            else:
                st.info("🔧 Inicializando o Chatbot...")
                cria_chain_conversa()
                st.rerun()

        # Aqui mantemos o "botao_quiz" no sidebar
        if st.button("🧪 Gerar Quiz com PDFs", use_container_width=True, key="botao_quiz"):
            from backend import importar_documentos, dividir_documentos, gerar_perguntas_quiz
            documentos = importar_documentos()
            documentos = dividir_documentos(documentos)
            st.session_state["quiz"] = gerar_perguntas_quiz(documentos)
            st.session_state["acertos"] = 0
            st.session_state["quiz_index"] = 0
            st.rerun()

    if "quiz" in st.session_state:
        quiz_window(st.session_state["quiz"])
    else:
        chat_window()

if __name__ == "__main__":
    main()
