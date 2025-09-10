# Plano: 0012-L - Finalização: Limpeza de Sessões Órfãs

## Contexto

O último passo para garantir a robustez do sistema, especialmente no modo `filesystem`, é a limpeza de sessões órfãs. Arquivos `session.json` podem ser deixados para trás se o processo for interrompido abruptamente.

Este plano implementa uma rotina de inicialização no Conductor que varre o workspace em busca de arquivos de sessão antigos e os remove.

## Checklist de Verificação

- [x] Criar uma nova função `cleanup_orphan_sessions(workspace_path: str)` em um módulo de utilitários de infraestrutura.
- [x] A função `cleanup_orphan_sessions` deve:
    1. Varrer recursivamente todos os diretórios de agentes dentro do `workspace_path`.
    2. Em cada diretório, procurar por um arquivo `session.json`.
    3. Se o arquivo `session.json` existir, verificar sua data de modificação.
    4. Se a data de modificação for mais antiga que um limite definido (ex: 24 horas), o arquivo deve ser removido.
- [x] Integrar a chamada `cleanup_orphan_sessions()` no processo de inicialização principal do Conductor (ex: no início do `cli/admin.py`), para que seja executada sempre que a aplicação iniciar.
- [x] A lógica deve ser executada apenas se o backend configurado for `filesystem`.
