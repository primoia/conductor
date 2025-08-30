#!/bin/bash

# Verifica se o texto foi passado como argumento
if [ -z "$1" ]; then
  echo "Uso: $0 \"Seu texto para resumir\""
  exit 1
fi

TEXT_TO_SUMMARIZE="$1"

# Configurações do Google Cloud (substitua pelos seus valores)
# Estes são os valores que usamos no teste, você pode ajustá-los se necessário.
GCP_PROJECT_ID="gen-lang-client-0338424173"
GCP_LOCATION="us-central1"
GCP_KEY_PATH_HOST="/home/cezar/.gcp/keys/conductor-key.json" # Caminho da chave na sua máquina

# Nome da imagem Docker que criamos
DOCKER_IMAGE_NAME="conductor-poc"

# Comando Docker para executar o Gemini CLI (agora instalado globalmente)
docker run --rm --user $(id -u):$(id -g) \
  -v "${GCP_KEY_PATH_HOST}:/gcp_key.json" \
  -v "/mnt/ramdisk/develop/nex-web-backend:/app" \
  -e "GOOGLE_APPLICATION_CREDENTIALS=/gcp_key.json" \
  -e "GOOGLE_GENAI_USE_VERTEXAI=true" \
  -e "GOOGLE_CLOUD_PROJECT=${GCP_PROJECT_ID}" \
  -e "GOOGLE_CLOUD_LOCATION=${GCP_LOCATION}" \
  "${DOCKER_IMAGE_NAME}" \
  gemini --yolo -p "${TEXT_TO_SUMMARIZE}" # Flag --yolo adicionada
