# SAGA 012: Desacoplamento e Reutilização da Camada de CLI

**Autor:** Primo (Gemini)
**Status:** Planejado

## 1. Missão

Esta saga executa uma refatoração crítica da camada de Interface de Linha de Comando (CLI). O objetivo é resolver a duplicação de código e a baixa coesão dos scripts `admin.py` e `agent.py`, transformando-os em pontos de entrada "finos" que orquestram um conjunto de componentes de UI compartilhados e reutilizáveis.

## 2. Justificativa

A complexidade e a duplicação de código nos scripts da CLI estavam se tornando um débito técnico significativo, dificultando a manutenção e a adição de novas funcionalidades. Esta refatoração aplica os princípios de design DRY (Don't Repeat Yourself) e SRP (Single Responsibility Principle) para criar uma base de código mais limpa, profissional e escalável.

## 3. Plano de Execução

O plano de implementação detalhado para esta refatoração está documentado no seguinte blueprint, que servirá como guia para a IA implementadora:

➡️ **[Plano de Refatoração Detalhado](./REFACTOR_PLAN_CLI.md)**
