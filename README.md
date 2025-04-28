
docker run -p 8501:8501 minha-app-streamlit



docker rm -f sofia_llm_agent

docker image rm -f sofia_llm_agent

docker build --no-cache -t sofia_llm_agent .

docker run --env-file .env --name sofia_llm_agent -p 8501:8501 --restart always --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 -d sofia_llm_agent