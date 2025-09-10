# Especificação Técnica e Plano de Execução: 0024-realizar-analise-seguranca

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa garante que a poderosa funcionalidade de plugins não introduza riscos de segurança inaceitáveis. Ao implementar salvaguardas básicas e documentar as considerações de segurança, demonstramos uma abordagem proativa à segurança e protegemos os usuários contra as vulnerabilidades mais comuns de carregamento dinâmico de código.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Foco em Path Traversal:** A principal salvaguarda a ser implementada no código **DEVE** ser a prevenção de Path Traversal, garantindo que os plugins só possam ser carregados de locais esperados.
- **Comunicação Clara:** Um aviso de segurança claro **DEVE** ser logado quando plugins externos são carregados.
- **Documentação:** As descobertas e as mitigações **DEVEM** ser documentadas em um novo arquivo de arquitetura.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar um arquivo existente e criar um novo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Modificar): `src/core/conductor_service.py`**
```python
# src/core/conductor_service.py
# ... (imports existentes, especialmente Path) ...
import logging # Adicionar import de logging

logger = logging.getLogger(__name__)

class ConductorService(IConductorService):
    # ... (__init__ e outros métodos) ...

    def load_tools(self) -> None:
        # ... (lógica de carregar Core Tools) ...

        # Carregar Tool Plugins
        project_root = Path().resolve()
        for plugin_path_str in self._config.tool_plugins:
            plugin_path = Path(plugin_path_str).resolve()

            # Medida de Segurança: Prevenção de Path Traversal
            if project_root not in plugin_path.parents:
                 logger.error(
                    f"Recusando carregar plugin de diretório não confiável: {plugin_path}. "
                    f"O caminho do plugin deve estar dentro do diretório do projeto."
                 )
                 continue
            
            if not plugin_path.is_dir():
                logger.warning(f"Caminho do plugin não é um diretório: {plugin_path}")
                continue
            
            logger.warning(f"Carregando plugins do diretório externo: {plugin_path}")
            
            # ... (resto da lógica de importação dinâmica) ...
```

**Arquivo 2 (Novo): `docs/architecture/SECURITY_ANALYSIS.md`**
```markdown
# Análise de Segurança da Arquitetura (SAGA-017)

## Vetor de Ameaça: Carregamento de Tool Plugins

A funcionalidade de `tool_plugins` introduzida na SAGA-016 permite carregar código Python de diretórios especificados no `config.yaml`. Isso representa o principal vetor de ameaça da nova arquitetura.

### Riscos Identificados

1.  **Path Traversal:** Um usuário mal-intencionado poderia configurar um caminho como `../../../../etc/` para tentar carregar ou inspecionar arquivos do sistema.
2.  **Execução de Código Malicioso:** Um usuário pode, intencionalmente ou não, apontar para um diretório de plugin que contém código malicioso, que seria executado na inicialização do `ConductorService`.

### Mitigações Implementadas (Estágio 24)

1.  **Validação de Caminho:** O `ConductorService` agora verifica se o caminho absoluto do diretório do plugin é um subdiretório do diretório do projeto. Isso mitiga efetivamente os ataques de Path Traversal, garantindo que apenas o código dentro do escopo do projeto possa ser carregado dinamicamente.
2.  **Logging Explícito:** Um `WARNING` é explicitamente logado sempre que um plugin é carregado. Isso aumenta a visibilidade e ajuda na auditoria.

### Riscos Residuais e Recomendações

-   O risco de execução de código malicioso persiste. A responsabilidade final recai sobre o operador que configura o `config.yaml`.
-   **Recomendação:** A documentação deve instruir claramente os usuários a **nunca** carregar plugins de fontes não confiáveis.
-   **Futuro:** Em um ambiente de produção mais restrito, considerar a implementação de uma "allow-list" de plugins permitidos ou a assinatura de código para os plugins.
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o `conductor_service.py` for modificado com a verificação de segurança e o arquivo `SECURITY_ANALYSIS.md` for criado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
