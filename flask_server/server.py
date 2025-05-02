import os
from flask import Flask, send_from_directory, render_template_string, request

app = Flask(__name__)

# Diretório onde os relatórios são salvos
RELATORIO_DIR = os.path.join(os.path.dirname(__file__), '..', 'relatorioQuiz')

# Rota para servir o relatório
@app.route('/relatorio/<nome_arquivo>')
def ver_relatorio(nome_arquivo):
    """
    Rota para acessar o relatório HTML gerado.
    :param nome_arquivo: Nome do arquivo HTML gerado
    """
    return send_from_directory(RELATORIO_DIR, nome_arquivo)


@app.route('/buscar', methods=['GET', 'POST'])
def index():
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Buscar Relatório</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                padding: 30px;
            }
            .container {
                max-width: 400px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            input[type="text"] {
                width: 100%;
                padding: 10px;
                margin-bottom: 15px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔎 Buscar Atividades</h2>
            <h4> Digite o nome do arquivo ou do aluno</h4>
           <form action="/resultado" method="get">
                <input type="text" name="matricula" placeholder="Digite a matrícula" required>
                <button type="submit">Buscar</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/resultado')
def resultado():
    matricula = request.args.get('matricula', '').strip()
    if not matricula:
        return "Matrícula não informada."

    try:
        arquivos = os.listdir(RELATORIO_DIR)
    except FileNotFoundError:
        return "Diretório de relatórios não encontrado."

    encontrados = [arq for arq in arquivos if matricula in arq]

    if not encontrados:
        return f"Nenhum relatório encontrado para a matrícula: {matricula}"

    links = "".join(
        f'<li><a href="/relatorio/{arq}" target="_blank">{arq}</a></li>' for arq in encontrados
    )

    return f'''
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 30px;
                    color: #333;
                }}
                h2 {{
                    color: #005ca9;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                li {{
                    margin: 10px 0;
                }}
                a {{
                    text-decoration: none;
                    color: #ff8c00;
                    font-weight: bold;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .back {{
                    display: inline-block;
                    margin-top: 20px;
                    padding: 10px 15px;
                    background-color: #005ca9;
                    color: white;
                    border-radius: 5px;
                    text-decoration: none;
                }}
                .back:hover {{
                    background-color: #003f73;
                }}
            </style>
        </head>
        <body>
            <h2>Atividades Encontradas: {matricula}</h2>
            <ul>{links}</ul>
            <a class="back" href="/buscar">Voltar</a>
        </body>
    </html>
    '''








# Executar a aplicação
if __name__ == '__main__':
    app.run(debug=True, port=5000)
