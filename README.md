



docker rm -f assistente_de_ensino

docker image rm -f assistente_de_ensino

docker build --no-cache -t assistente_de_ensino .

docker run --env-file .env --name assistente_de_ensino -p 8501:8501 --restart always --log-driver=json-file --log-opt max-size=10m --log-opt max-file=3 -d assistente_de_ensino