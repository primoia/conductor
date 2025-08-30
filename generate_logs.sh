#!/bin/bash

# Script para gerar logs contínuos para teste da stack Loki/Grafana
# Executa por 5 minutos gerando logs a cada 5 segundos

echo "Iniciando geração contínua de logs..."
echo "Pressione Ctrl+C para parar"

# Contador para logs únicos
counter=1
end_time=$(($(date +%s) + 300)) # 5 minutos = 300 segundos

while [ $(date +%s) -lt $end_time ]; do
    timestamp=$(date -Iseconds)
    
    # Array de tipos de logs para variar
    log_types=(
        "INFO: Processamento batch #$counter executado com sucesso - $timestamp"
        "WARN: Cache miss detectado para key user_$counter - $timestamp" 
        "ERROR: Timeout na conexão com serviço externo - tentativa $counter - $timestamp"
        "DEBUG: Query executada em $(($counter * 23))ms - SELECT * FROM agents WHERE active=true - $timestamp"
        "METRICS: Requests/sec: $((50 + $counter % 20)), Memory: $((400 + $counter % 100))MB - $timestamp"
        "AUDIT: User admin executou ação CREATE_AGENT em $timestamp"
        "PERFORMANCE: Response time: $(($counter * 12))ms for endpoint /api/status - $timestamp"
    )
    
    # Seleciona um tipo de log aleatório
    log_type=${log_types[$((counter % ${#log_types[@]}))]}
    
    # Gera o log diretamente para stdout e arquivo
    echo "$log_type" | tee -a /app/logs/conductor.log
    
    echo "Log $counter enviado: $(date)"
    
    # Incrementa contador
    counter=$((counter + 1))
    
    # Aguarda 5 segundos
    sleep 5
done

echo "Geração de logs concluída após 5 minutos"