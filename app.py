import streamlit as st
import time
from backend import cria_chain_conversa, folder_files
from pathlib import Path
import uuid
import random
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

from datetime import datetime
import webbrowser
from utils.avaliador import analisar_desempenho_ia

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
        section[data-testid="stSidebar"] {
            background-color: #ffe5b4; /* laranja claro */
        }
        .stButton>button:hover {
            background-color: #004085; /* Cor do botão ao passar o mouse */
        }
             summary {
            color: #ff7f00 !important; /* laranja escuro para visibilidade */
            font-size: 18px !important;
        }

        /* Aumenta a espessura da seta */
        summary::marker {
            color: #ff7f00 !important;
            font-size: 20px;
        }

        /* Aumenta contraste no modo escuro também */
        @media (prefers-color-scheme: dark) {
            section[data-testid="stSidebar"] {
                background-color: #cc8a3e;
            }
            summary {
                color: #fff7e6 !important;
            }
            summary::marker {
                color: #fff7e6 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

def chat_window():
    st.markdown("## 🤖 **Assistente de Ensino**")
    st.markdown(" * Insira arquivos PDF para transformar seu material em conhecimento interativo.")
    st.markdown(" * Converse com nosso agente de ensino e teste seu aprendizado em quizzes personalizados.")
   
    st.markdown("---")

    if 'chain' not in st.session_state:
        st.warning("📄 Insira arquivo na barra lateral para iniciar")
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
                st.image("pdfs/loading.gif", width=50)

                resposta = chain.invoke({"question": nova_mensagem})  # Guarda a resposta

                if isinstance(resposta, dict) and "answer" in resposta:
                    resposta_texto = resposta["answer"]
                else:
                    resposta_texto = str(resposta)

                # Exibe a resposta antes de recarregar
                st.markdown(resposta_texto)

            st.rerun()
def display_existing_files(folder):
    session_id = st.session_state.get("session_id", "")

    # Só pega os PDFs da sessão atual
    arquivos = list(folder.glob(f"*_{session_id}.pdf"))

    # if arquivos:
    #     st.markdown("### Arquivos já enviados:")
    #     for arquivo in arquivos:
    #         col1, col2 = st.columns([4, 1])
    #         with col1:
    #             # Remove o session_id do nome exibido
    #             nome_original = arquivo.name.replace(f"_{session_id}", "")
    #             st.markdown(f"- {nome_original}")
    #         with col2:
    #             if st.button(f"❌", key=arquivo.name):
    #                 excluir_arquivo(arquivo)
    #                 st.rerun()
    # else:
    #     st.warning("⚠️ Insira PDFs das aulas e clique em inicializar chat.")


def excluir_arquivo(arquivo):
    try:
        arquivo.unlink()
        st.success(f"✅ Arquivo {arquivo.name} excluído com sucesso!")
    except Exception as e:
        st.error(f"❌ Erro ao excluir o arquivo {arquivo.name}: {str(e)}")

def quiz_window(perguntas_raw):
    st.markdown("## 🧠 Quiz para testar seu conhecimento")

    if "acertos" not in st.session_state:
        st.session_state["acertos"] = 0
    if "respostas_usuario" not in st.session_state:
        st.session_state["respostas_usuario"] = []

    respostas_usuario = st.session_state["respostas_usuario"]  # <- Corrigido

    perguntas_brutas = perguntas_raw.strip().split("\n\nPergunta:")
    if perguntas_brutas[0].startswith("Pergunta:"):
        perguntas_brutas[0] = perguntas_brutas[0][len("Pergunta:"):]

    for idx, pergunta_raw in enumerate(perguntas_brutas):
        linhas = pergunta_raw.strip().split("\n")

        if len(linhas) < 7:
            st.warning(f"⚠️ Verifique se tem arquivo anexado")
            continue

        pergunta_texto = linhas[0]
        opcoes = linhas[1:5]
        resposta_certa = linhas[5].split(":")[-1].strip().upper()[0]
        explicacao = linhas[6].split(":", 1)[-1].strip()

        st.markdown(f"**Pergunta {idx + 1}:** {pergunta_texto}")
        escolha = st.radio("Escolha uma opção:", opcoes, index=None, key=f"resposta_{idx}")

        correta = False
        letra_escolhida = ""
        if escolha:
            letra_escolhida = escolha[0].upper()
            correta = (letra_escolhida == resposta_certa)
        else:
            letra_escolhida = "Nenhuma"

        if f"resposta_mostrada_{idx}" not in st.session_state:
            st.session_state[f"resposta_mostrada_{idx}"] = False

        if st.button(f"Enviar Resposta {idx + 1}", key=f"ver_resposta_{idx}"):
            st.session_state[f"resposta_mostrada_{idx}"] = True
            if correta:
                st.session_state["acertos"] += 1

        if st.session_state[f"resposta_mostrada_{idx}"]:
            index_resposta_certa = ord(resposta_certa) - ord("A")
            texto_resposta = opcoes[index_resposta_certa][3:].strip() if 0 <= index_resposta_certa < len(opcoes) else "opção desconhecida"

            if correta:
                st.success(f"✅ Resposta correta! {resposta_certa}) {texto_resposta}")
            else:
                st.error(f"❌ Resposta incorreta. A correta é **{resposta_certa}**) {texto_resposta}")

            st.markdown(f"🧠 **Explicação:** {explicacao}")
            st.markdown("________________________________")

            # Salvar apenas se ainda não foi salvo
            ja_registrada = any(r["pergunta"] == pergunta_texto for r in respostas_usuario)
            if not ja_registrada:
                respostas_usuario.append({
                    "pergunta": pergunta_texto,
                    "resposta_usuario": letra_escolhida,
                    "resposta_correta": resposta_certa,
                    "correta": correta,
                    "explicacao": explicacao
                })

    st.markdown(f"### 🎯 Total de acertos: {st.session_state['acertos']} de {len(perguntas_brutas)} perguntas.")


    respostas_usuario = st.session_state.get("respostas_usuario", [])
    todas_preenchidas = all(r.get("resposta_usuario") for r in respostas_usuario)
    
# Exibe o botão somente se todas estiverem preenchidas
    if todas_preenchidas:
    # Botão para salvar relatório com IA
     if st.button("Ao concluir salve o simulado", use_container_width=True):
        import os
        import webbrowser
        from datetime import datetime

        os.makedirs("relatorioQuiz", exist_ok=True)
        data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        caminho_html = f"relatorioQuiz/relatorio_{data_hora}.html"

        respostas_usuario = st.session_state['respostas_usuario']
        perguntas_brutas = st.session_state.get('perguntas_brutas', [])
        feedback_ia = analisar_desempenho_ia(respostas_usuario)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Relatório do Quiz - {data_hora}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f4f6f9;
                    color: #333;
                    padding: 30px;
                    line-height: 1.6;
                }}
                h1, h2 {{
                    color: #2c3e50;
                }}
                .card {{
                    background: #fff;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .separador {{
                    border-top: 1px solid #ccc;
                    margin: 20px 0;
                }}
                .correta {{ color: green; }}
                .incorreta {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>📊 Relatório do Quiz - {data_hora}</h1>
            <div class="card">
                <p><strong>✅ Acertos:</strong> {st.session_state['acertos']}</p>
            </div>

            <div class="card">
                <h2>🧠 Análise do Desempenho (IA)</h2>
                  {''.join(f'<p>{paragrafo}</p>' for paragrafo in feedback_ia.split('\n\n'))}
            </div>

            <h2>📋 Respostas do Quiz</h2>
        """

        for i, r in enumerate(respostas_usuario):
            html_content += f"""
            <div class="card">
                <p><strong>Pergunta {i+1}:</strong> {r['pergunta']}</p>
                <p><strong>Sua resposta:</strong> {r['resposta_usuario']}</p>
                <p><strong>Resposta correta:</strong> {r['resposta_correta']}</p>
                <p><strong>Resultado:</strong> <span class="{ 'correta' if r['correta'] else 'incorreta' }">
                    {"Correta" if r['correta'] else 'Incorreta'}
                </span></p>
                <p><strong>Explicação:</strong> {r['explicacao']}</p>
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        with open(caminho_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        st.success("✅ Relatório salvo com sucesso!")
        with open(caminho_html, "r", encoding="utf-8") as file:
            html_string = file.read()
            st.download_button(
             label="📄 Baixar Relatório em HTML",
             data=html_string,
             file_name=f"relatorio_{data_hora}.html",
             mime="text/html"
            )


    # if st.button("🔁 Refazer Quiz com PDFs", use_container_width=True, key="botao_quiz_refazer"):
    #     st.session_state.pop("quiz", None)
    #     st.session_state.pop("respostas_usuario", None)
    #     st.session_state["acertos"] = 0
    #     from backend import importar_documentos, dividir_documentos, gerar_perguntas_quiz
    #     documentos = importar_documentos()
    #     documentos = dividir_documentos(documentos)
    #     st.session_state["quiz"] = gerar_perguntas_quiz(documentos)
    #     st.rerun()

def save_uploaded_files(uploaded_files, folder):
    # Apaga arquivos antigos da sessão
    for file in folder.glob(f"*_{st.session_state['session_id']}.pdf"):
        file.unlink()

    # Salva novos arquivos com o ID da sessão
    for file in uploaded_files:
        filename = file.name.replace(".pdf", f"_{st.session_state['session_id']}.pdf")
        (folder / filename).write_bytes(file.read())


def main():
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(random.randint(100000, 999999))

    with st.sidebar:
        st.image("pdfs/logomarca.png", width=200)

       
        st.markdown("""
    <style>
        .custom-upload label {
            background-color: #0056b3;
            color: white !important;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 16px;
            text-align: center;
            display: inline-block;
            width: 100%;
            cursor: pointer;
        }
        .custom-upload label:hover {
            background-color: #00408d;
        }
        .custom-upload .stFileUploader {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

        st.markdown("### 📄Envie PDfs de livros, aulas ou documentos")
        st.markdown("Arraste e solte os arquivos aqui ou clique para selecionar manualmente.")

        uploaded_pdfs = st.file_uploader(
        label="",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Você pode adicionar vários arquivos ao mesmo tempo."
    )

        if uploaded_pdfs:
            save_uploaded_files(uploaded_pdfs, folder_files)
            st.success(f"✅ {len(uploaded_pdfs)} arquivo(s) salvo(s) com sucesso!")

        # Mostrar arquivos existentes (retorna uma lista de arquivos)
        session_id = st.session_state.get("session_id", "")
        arquivos_existentes = list(folder_files.glob(f"*_{session_id}.pdf"))
        display_existing_files(folder_files)

        # Só mostra os botões se houver pelo menos 1 PDF
        if len(arquivos_existentes) > 0:
            label_botao = "▶️ Inicializar Chatbot" if "chain" not in st.session_state else "🔄 Atualizar Chatbot"
            with st.container():
                st.markdown('<div class="bot-container">', unsafe_allow_html=True)

                if st.button(label_botao, use_container_width=True, key="botao_inicializar"):
                    st.info("🔧 Inicializando o Chatbot...")
                    cria_chain_conversa()
                    st.session_state.pop("quiz", None)
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
        else:
            st.info("📄 Nenhum PDF encontrado. Faça upload para habilitar o chat e o quiz")


                            
        resposta = st.radio(
    "Caso Não tenha material para upload agora, selecione uma aula para testar a aplicação",
    ["Vou enviar um material", "Aula de leitura dinâmica","Aula de Marketing de vendas"],
    index=0
    )

    if resposta == "Aula de leitura dinâmica":
            from shutil import copyfile

            session_id = st.session_state["session_id"]
            origem = Path("files/LIVRO LEITURA DINÂMICA_617127.pdf")
            destino = folder_files / f"LIVRO LEITURA DINÂMICA_{session_id}.pdf"

            if not destino.exists():  # Evita duplicação
                copyfile(origem, destino)
                st.success("✅ Arquivo de exemplo carregado com sucesso!")
                st.rerun()


    if resposta == "Aula de Marketing de vendas":
            from shutil import copyfile

            session_id = st.session_state["session_id"]
            origem = Path("files/5ca0e9_424413178c6f4e218770dc8a08208fef_826388.pdf")
            destino = folder_files / f"5ca0e9_424413178c6f4e218770dc8a08208fef_{session_id}.pdf"

            if not destino.exists():  # Evita duplicação
                copyfile(origem, destino)
                st.success("✅ Arquivo de exemplo carregado com sucesso!")
                st.rerun()

    # Botão para pesquisa de usuário
    st.markdown("""
        <style>
            .orange-button {
                background-color: #fe9f8b;
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
            }
            .orange-button:active {
                background-color: orangered;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        '<a class="orange-button" href="https://docs.google.com/forms/d/e/1FAIpQLSd7IhxE0Q5kmX4TF9m1LIpswwqhD6IAXYaAPP49p7tE26CVxw/viewform?usp=dialog" target="_self">👤 Após testar o chat e o quiz responda a pesquisa do usuário aqui</a>',
        unsafe_allow_html=True
    )

    if "quiz" in st.session_state:
        quiz_window(st.session_state["quiz"])
    else:
        chat_window()

if __name__ == "__main__":
    main()
