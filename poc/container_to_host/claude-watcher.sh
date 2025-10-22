#!/bin/bash

# Claude File Watcher - Monitora arquivos de input e executa claude
# Uso: ./claude-watcher.sh

INPUT_DIR="/tmp/claude-input"
OUTPUT_DIR="/tmp/claude-output"
LOG_FILE="/tmp/claude-watcher.log"

# Criar diretórios se não existirem
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

echo "$(date): Claude Watcher iniciado" >> "$LOG_FILE"
echo "$(date): Monitorando: $INPUT_DIR" >> "$LOG_FILE"
echo "$(date): Saída em: $OUTPUT_DIR" >> "$LOG_FILE"

echo "🚀 Claude Watcher iniciado!"
echo "📁 Input:  $INPUT_DIR"
echo "📁 Output: $OUTPUT_DIR"
echo "📝 Log:    $LOG_FILE"
echo ""
echo "Aguardando arquivos JSON..."

while true; do
    # Verificar se há arquivos .json no diretório de entrada
    for request_file in "$INPUT_DIR"/*.json; do
        # Verificar se o arquivo realmente existe (evita problema com glob vazio)
        [ -f "$request_file" ] || continue

        # Extrair ID do arquivo
        request_id=$(basename "$request_file" .json)
        output_file="$OUTPUT_DIR/${request_id}.json"

        echo "📨 Processando: $request_id"
        echo "$(date): Processando request $request_id" >> "$LOG_FILE"

        # Verificar se é um JSON válido
        if ! jq empty "$request_file" 2>/dev/null; then
            echo "❌ JSON inválido: $request_id"
            echo '{"status": "error", "error": "JSON inválido"}' > "$output_file"
            rm "$request_file"
            continue
        fi

        # Ler comando e cwd do JSON
        command_array=$(jq -r '.command[]?' "$request_file" 2>/dev/null)
        cwd=$(jq -r '.cwd // "."' "$request_file" 2>/dev/null)

        if [ -z "$command_array" ]; then
            echo "❌ Comando vazio: $request_id"
            echo '{"status": "error", "error": "Campo command é obrigatório"}' > "$output_file"
            rm "$request_file"
            continue
        fi

        # Construir comando
        command=""
        while IFS= read -r line; do
            if [ -n "$command" ]; then
                command="$command $line"
            else
                command="$line"
            fi
        done <<< "$command_array"

        echo "🔧 Comando: $command"
        echo "📂 CWD: $cwd"

        # Verificar se o diretório existe
        if [ ! -d "$cwd" ]; then
            echo "❌ Diretório não existe: $cwd"
            echo "{\"status\": \"error\", \"error\": \"Diretório não encontrado: $cwd\"}" > "$output_file"
            rm "$request_file"
            continue
        fi

        # Executar claude no diretório especificado
        echo "⚡ Executando claude..."
        start_time=$(date +%s)

        (
            cd "$cwd" || exit 1
            timeout 600 $command 2>&1
        ) > "/tmp/claude-temp-$request_id.txt" 2>&1

        exit_code=$?
        end_time=$(date +%s)
        duration=$((end_time - start_time))

        # Ler resultado
        if [ -f "/tmp/claude-temp-$request_id.txt" ]; then
            result=$(cat "/tmp/claude-temp-$request_id.txt")
            rm "/tmp/claude-temp-$request_id.txt"
        else
            result=""
        fi

        # Criar resposta JSON
        if [ $exit_code -eq 0 ]; then
            status="success"
            echo "✅ Sucesso em ${duration}s"
        elif [ $exit_code -eq 124 ]; then
            status="timeout"
            result="Comando excedeu tempo limite de 600s (10 minutos)"
            echo "⏰ Timeout em ${duration}s"
        else
            status="error"
            echo "❌ Erro (código $exit_code) em ${duration}s"
        fi

        # Escapar o resultado para JSON
        result_escaped=$(echo "$result" | jq -Rs .)

        # Salvar resultado
        cat > "$output_file" << EOF
{
    "status": "$status",
    "result": $result_escaped,
    "exit_code": $exit_code,
    "duration": $duration,
    "request_id": "$request_id"
}
EOF

        echo "$(date): Request $request_id processado - status: $status, duration: ${duration}s" >> "$LOG_FILE"

        # Remover arquivo de entrada
        rm "$request_file"

        echo "💾 Resultado salvo: ${request_id}.json"
        echo ""
    done

    # Aguardar um pouco antes de verificar novamente
    sleep 0.5
done