from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # ou defina direto como string

def analisar_desempenho_ia(respostas_usuario):
    resumo_respostas = ""
    for idx, r in enumerate(respostas_usuario, start=1):
        status = "Correta" if r["correta"] else "Incorreta"
        resumo_respostas += (
            f"Pergunta {idx}:\n"
            f"- Enunciado: {r['pergunta']}\n"
            f"- Resposta do aluno: {r['resposta_usuario']}\n"
            f"- Resposta correta: {r['resposta_correta']} ({status})\n"
            f"- Explicação da resposta correta: {r['explicacao']}\n\n"
        )
    prompt = (
        "Você é um professor experiente e especializado em elaborar feedbacks pedagógicos personalizados. "
        "Abaixo estão as perguntas e respostas de um aluno em um quiz, incluindo as explicações para cada questão. "
        "Sua tarefa é analisar profundamente esse desempenho.\n\n"
        "Para cada resposta incorreta:\n"
        "- Explique por que a resposta correta é a mais adequada, reforçando o conteúdo da explicação.\n"
        "- Aponte onde está o erro de interpretação ou conhecimento do aluno.\n"
        "- Sugira formas de aprender melhor esse conteúdo, como técnicas de estudo, tópicos que o aluno deve revisar, livros, sites confiáveis ou videoaulas.\n\n"
        "Para as respostas corretas:\n"
        "- Elogie e destaque o entendimento correto do aluno de forma positiva.\n"
        "- Reforce brevemente por que aquela resposta está certa.\n\n"
        "Ao final:\n"
        "- Resuma os principais pontos fortes do aluno.\n"
        "- Aponte as principais dificuldades.\n"
        "- Dê orientações gerais e práticas para evolução no aprendizado com base no desempenho.\n\n"
        f"{resumo_respostas}\n"
        "Agora escreva um feedback claro, didático, detalhado e com tom motivador:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ocorreu um erro ao gerar o feedback com IA: {str(e)}"
