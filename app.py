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

# Adicionando estilo CSS
st.markdown("""
    <style>
     
        .stButton>button {
            background-color: #0056b3; /* Cor do botão azul */
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
        }
        .stButton>button:hover {
            background-color: #004085; /* Cor do botão ao passar o mouse */
        }
    </style>
""", unsafe_allow_html=True)

def chat_window():
    st.markdown("## 🤖 **Assistente de ensino**")
   
    st.markdown(" **Insira PDFs, Estude com o chat, Teste seus conhecimentos no quiz **")
    
    st.markdown("---")

    if 'chain' not in st.session_state:
        st.warning("📄Insira Pdfs das aulas e clique em inicializar Chat.")
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
    arquivos = list(folder.glob("*.pdf"))
    if arquivos:
        st.markdown("### Arquivos já enviados:")
        for arquivo in arquivos:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"- {arquivo.name}")
            with col2:
                if st.button(f"❌", key=arquivo.name):
                    excluir_arquivo(arquivo)
                    st.rerun()
    else:
        st.warning("⚠️ Insira PDFs das aulas e clique em inicializar chat.")

def excluir_arquivo(arquivo):
    try:
        arquivo.unlink()
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
        resposta_certa = linhas[5].split(":")[-1].strip().upper()[0]

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
        st.image("pdfs/logomarca.png", width=200)
        
        label_botao = "▶️ Inicializar Chatbot" if "chain" not in st.session_state else "🔄 Atualizar Chatbot"

        
        

        with st.container():  # Aplicando o fundo azul aos botões
            st.markdown('<div class="bot-container">', unsafe_allow_html=True)
            if st.button(label_botao, use_container_width=True, key="botao_inicializar"):
                if len(list(folder_files.glob("*.pdf"))) == 0:
                    st.error("⚠️ Adicione arquivos PDF antes de inicializar o chatbot.")
                else:
                    st.info("🔧 Inicializando o Chatbot...")
                    cria_chain_conversa()
                    st.rerun()

            if st.button("🧪 Gerar quiz para testar seu conhecimento", use_container_width=True, key="botao_quiz"):
                from backend import importar_documentos, dividir_documentos, gerar_perguntas_quiz
                documentos = importar_documentos()
                documentos = dividir_documentos(documentos)
                st.session_state["quiz"] = gerar_perguntas_quiz(documentos)
                st.session_state["acertos"] = 0
                st.session_state["quiz_index"] = 0
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

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


   # st.button("👤 Após testar o chat e o quiz responda a pesquisa do usuário", 
    #      on_click=lambda: st.write("Redirecionando para www.senac.br"))

    



# Estilizando o botão com CSS
    st.markdown("""
    <style>
        .orange-button {
            background-color: orange;
            color: black !important;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            text-align: center;
            display: inline-block;
            text-decoration: none !important;
            font-family: inherit;
        }
        .orange-button:hover {
            background-color: darkorange;
            text-decoration: none !important;
        }
        .orange-button:visited {
            color: black !important;
            text-decoration: none !important;
        }
        .orange-button:active {
            background-color: orangered;
            text-decoration: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Criando o link estilizado como botão
    st.markdown(
    '<a class="orange-button" href="https://docs.google.com/forms/d/e/1FAIpQLSd7IhxE0Q5kmX4TF9m1LIpswwqhD6IAXYaAPP49p7tE26CVxw/viewform?usp=dialog" target="_self">👤 Após testar o chat e o quiz responda a pesquisa do usuário</a>',
    unsafe_allow_html=True
    )


    


    


   

    
        

    if "quiz" in st.session_state:
        quiz_window(st.session_state["quiz"])
    else:
        chat_window()

if __name__ == "__main__":
    main()
