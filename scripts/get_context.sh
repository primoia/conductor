#!/bin/bash
#
# Este script monta um prompt de contexto estratégico para o projeto Conductor.
# Ele suporta diferentes níveis de detalhe para se adaptar a diferentes IAs.
#
# Uso:
#   ./scripts/get_context.sh | claude -p - "Pergunta superficial"
#   ./scripts/get_context.sh --level deep | gemini -p - "Pergunta profunda"

set -e

# --- Configuração ---
LEVEL="surface" # Nível padrão

# --- Parsing de Argument-e ---
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -l|--level) LEVEL="$2"; shift ;;
        *) echo "Parâmetro desconhecido: $1"; exit 1 ;;
    esac
    shift
done

# --- Lógica Principal ---

# Navega para a raiz do projeto Conductor a partir da localização do script
cd "$(dirname "$0")/.."

echo "# CONTEXTO DO PROJETO CONDUCTOR (Nível: ${LEVEL})"
echo "---"
echo "## ESTRUTURA DE ARQUIVOS:"
if command -v tree &> /dev/null
then
    tree -L 3 docs/ project-management/
else
    echo "Comando 'tree' não encontrado. Usando 'find' como alternativa."
    find docs/ project-management/ -maxdepth 3 -print | sed -e 's;[^/]*/;|____;g;s;____|; |;g'
fi
echo "---"

if [ "$LEVEL" == "deep" ]; then
    echo "## CONTEÚDO DOS ARQUIVOS-CHAVE (PROFUNDO):"
    cat README.md \
        docs/DOCUMENTATION_GUIDE.md \
        docs/README.md \
        docs/guides/ONBOARDING_NEW_PROJECT.md \
        docs/architecture/GEMINI_ARCH_SPEC.md
else
    echo "## CONTEÚDO DOS ARQUIVOS-CHAVE (SUPERFICIAL):"
    cat README.md \
        docs/DOCUMENTATION_GUIDE.md
fi
