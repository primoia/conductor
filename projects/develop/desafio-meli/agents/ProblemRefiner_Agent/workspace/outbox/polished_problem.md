# Problema Polido: Implementação de Autenticação JWT para API E-commerce Spring Boot

## 1. Objetivo Principal

**Implementar sistema de autenticação JWT** para proteger uma API REST de e-commerce em Spring Boot que atualmente não possui nenhum controle de acesso, permitindo que qualquer pessoa execute operações GET/POST/DELETE em todos os recursos sem autenticação.

**Valor de Negócio**: Garantir segurança dos dados, controle de acesso adequado e proteção contra acesso não autorizado aos recursos da API.

## 2. Contexto Técnico

**API Atual - Estrutura Existente:**
- **Framework**: Spring Boot (sem Spring Security configurado)
- **Controllers**: 3 principais
  - `ProductController`: GET/POST /api/produtos
  - `UserController`: GET/POST/PUT/DELETE /api/usuarios  
  - `OrderController`: GET/POST /api/pedidos
- **Frontend**: React consumindo a API
- **Testes**: JUnit (aproximadamente 15 testes que serão impactados)

**Entidade User (Estrutura Atual):**
```
- id: Long
- email: String
- password: String (precisará ser hasheada)
- nome: String
- role: Enum (CLIENTE, ADMIN) - campo a ser adicionado
```

## 3. Requisitos e Restrições

### 3.1 Tipos de Usuário e Permissões

**CLIENTE:**
- ✅ GET /api/produtos (visualizar catálogo)
- ✅ POST /api/pedidos (criar pedidos)
- ✅ GET /api/pedidos (apenas seus próprios pedidos)
- ✅ GET /api/usuarios/{id} (apenas seu próprio perfil)
- ✅ PUT /api/usuarios/{id} (apenas seu próprio perfil)

**ADMIN:**
- ✅ Acesso total a todos os endpoints
- ✅ Pode fazer pedidos (para testes do sistema)
- ✅ Gerenciar usuários e produtos

### 3.2 Autenticação

**Endpoint de Login:**
- `POST /api/auth/login`
- Input: `{ "email": "user@example.com", "password": "senha123" }`
- Output: `{ "token": "jwt_token_here", "user": { "id": 1, "nome": "João", "role": "CLIENTE" } }`

**Configuração JWT:**
- Token expira em 1 hora
- Logout apenas no frontend (remoção do token)
- Refresh token não necessário (por enquanto)

### 3.3 Restrições Técnicas

- Spring Security deve ser integrado ao projeto existente
- 15 testes JUnit existentes serão impactados
- Estratégia de testes: `@WithMockUser` para autenticação nos testes
- Frontend React precisará ser atualizado para incluir token nas requisições

### 3.4 Regras de Negócio Específicas

1. **Isolamento de Dados**: Cliente nunca pode acessar pedidos de outros clientes
2. **Perfil Próprio**: Cliente só pode visualizar/editar seu próprio perfil
3. **Catálogo Público**: Produtos são visíveis para clientes autenticados
4. **Admin Total**: Admin tem acesso irrestrito para administração

## 4. Perguntas Pendentes

✅ **Resolvidas durante análise:**
- Estrutura da entidade User definida
- Permissões específicas por role esclarecidas  
- Estratégia de testes definida
- Configuração JWT especificada
- Regras de negócio para isolamento de dados confirmadas

**Nenhuma pergunta pendente identificada** - problema suficientemente detalhado para implementação.

## 5. Próximos Passos Recomendados

### Fase 1: Configuração Base
1. **Adicionar Spring Security** ao `pom.xml`
2. **Adicionar JWT library** (ex: `jjwt`)
3. **Atualizar entidade User** (adicionar campo `role`)
4. **Criar enum Role** (CLIENTE, ADMIN)

### Fase 2: Implementação Autenticação
5. **Criar JwtUtil** (geração/validação de tokens)
6. **Implementar AuthController** (`/api/auth/login`)
7. **Configurar Spring Security** (filtros JWT)
8. **Adicionar UserDetailsService**

### Fase 3: Autorização
9. **Implementar autorizações** nos controllers existentes
10. **Validar isolamento de dados** (cliente vs próprios recursos)
11. **Atualizar testes** com `@WithMockUser`

### Fase 4: Integração
12. **Atualizar frontend React** (headers Authorization)
13. **Testes end-to-end** com autenticação
14. **Documentação da API** atualizada

## 6. Impacto Estimado

**Arquivos a Modificar:**
- `pom.xml` (dependências)
- Entidade `User` 
- Controllers existentes (3 arquivos)
- Classes de configuração Spring Security (novas)
- 15 testes JUnit existentes
- Frontend React (integração)

**Complexidade**: Média - implementação padrão de JWT com Spring Security
**Tempo Estimado**: 2-3 dias de desenvolvimento + 1 dia de testes

---
**Histórico de Conversas**: 186 interações analisadas  
**Usuários Envolvidos**: João, Cezar  
**Data de Geração**: 2025-08-16  
**Status**: Problema completamente definido - Pronto para implementação