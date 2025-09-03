# SAGA 010: Observabilidade Centralizada com a Stack PLG

**Autor:** Primo (Gemini)
**Status:** Planejado

## 1. Missão

Esta saga estabelece uma stack de observabilidade centralizada para o ecossistema Primoia, começando pelo projeto `conductor`. O objetivo é agregar, visualizar e filtrar os logs estruturados de todos os agentes em execução, fornecendo uma visão clara e em tempo real do comportamento do sistema.

## 2. Justificativa

Com a refatoração da SAGA-009, a aplicação `conductor` agora produz logs JSON estruturados. No entanto, esses logs são efêmeros e isolados em seus respectivos containers. Para depurar, monitorar e entender o sistema como um todo, é essencial centralizá-los. A stack PLG (Promtail, Loki, Grafana) foi escolhida por sua eficiência, leveza e integração nativa com ambientes containerizados.

## 3. Plano de Execução

O plano de implementação detalhado, incluindo aprimoramentos de log, arquivos de configuração e orquestração Docker, está documentado no seguinte blueprint:

➡️ **[Plano de Implementação Detalhado](./IMPLEMENTATION_PLAN.md)**
