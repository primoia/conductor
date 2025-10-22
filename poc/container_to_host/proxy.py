# /mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/poc/container_to_host/proxy.py
from flask import Flask, request, jsonify
import subprocess
import logging
import os
import pty
import select

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='[ProxyHost] %(asctime)s - %(message)s')

app = Flask(__name__)

@app.route('/test', methods=['POST'])
def test_command():
    data = request.get_json()
    if not data or 'cwd' not in data:
        return jsonify({"status": "error", "stderr": "O campo 'cwd' é obrigatório."}), 400

    cwd = data['cwd']
    # Para este teste, o comando é fixo e simples: listar arquivos no diretório recebido.
    command = ["ls", "-la"]

    logging.info(f"Recebido pedido para executar '{' '.join(command)}' em '{cwd}'")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
            timeout=30,
        )

        logging.info(f"Comando executado. Código de retorno: {result.returncode}")

        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })

    except FileNotFoundError:
        logging.error(f"Erro: Diretório de trabalho não encontrado: {cwd}")
        return jsonify({"status": "error", "stderr": f"Diretório não encontrado: {cwd}"}), 404
    except Exception as e:
        logging.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({"status": "error", "stderr": str(e)}), 500

@app.route('/execute', methods=['POST'])
def execute_command():
    data = request.get_json()
    if not data or 'command' not in data or 'cwd' not in data:
        return jsonify({"status": "error", "stderr": "Os campos 'command' e 'cwd' são obrigatórios."}), 400

    command = data['command']
    cwd = data['cwd']
    timeout = data.get('timeout', 600)  # 10 minutes timeout for long-running operations

    logging.info(f"Recebido pedido para executar '{' '.join(command)}' em '{cwd}' via script")

    try:
        # Constrói o comando e configura ambiente de terminal completo
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'
        env['COLUMNS'] = '120'
        env['LINES'] = '30'
        env['TTY'] = '/dev/pts/0'

        # Usa script com configurações de terminal específicas
        command_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command)
        script_command = ['script', '-qec', command_str, '/dev/null']

        result = subprocess.run(
            script_command,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
            timeout=timeout,
            env=env
        )

        logging.info(f"Comando executado via script. Código de retorno: {result.returncode}")

        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        })

    except FileNotFoundError:
        logging.error(f"Erro: Diretório de trabalho não encontrado: {cwd}")
        return jsonify({"status": "error", "stderr": f"Diretório não encontrado: {cwd}"}), 404
    except subprocess.TimeoutExpired:
        logging.error(f"Comando excedeu o tempo limite de {timeout} segundos.")
        return jsonify({"status": "error", "stderr": f"Timeout: Comando excedeu {timeout}s."}), 408
    except Exception as e:
        logging.error(f"Erro inesperado: {e}", exc_info=True)
        return jsonify({"status": "error", "stderr": str(e)}), 500

if __name__ == '__main__':
    # Roda na porta 9091, acessível por qualquer IP na máquina (0.0.0.0)
    app.run(host='0.0.0.0', port=9091)