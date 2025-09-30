# /mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/poc/container_to_host/test_proxy.py
import requests
import os

# O DNS especial que aponta para a máquina host de dentro de um contêiner Docker
PROXY_URL = "http://host.docker.internal:9090/test"

# O diretório no HOST que queremos testar (pode ser pego de uma variável de ambiente)
TARGET_DIR_ON_HOST = os.getenv("TARGET_DIR", "/mnt/ramdisk/develop")

print(f"[Container] Tentando chamar o proxy em: {PROXY_URL}")
print(f"[Container] Testando o diretório do host: {TARGET_DIR_ON_HOST}")

try:
    response = requests.post(PROXY_URL, json={"cwd": TARGET_DIR_ON_HOST}, timeout=10)
    response.raise_for_status() # Lança um erro para status codes 4xx/5xx

    print("\n[Container] --- SUCESSO! RESPOSTA DO PROXY ---")
    print(response.json())
    print("[Container] ------------------------------------")

except requests.exceptions.RequestException as e:
    print(f"\n[Container] --- ERRO! NÃO FOI POSSÍVEL CONECTAR AO PROXY ---")
    print(f"[Container] Erro: {e}")
    print("[Container] Verifique se o proxy.py está rodando no host e se o firewall não está bloqueando a porta 9090.")
    print("[Container] -------------------------------------------------")