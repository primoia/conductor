# Golden Master Testing

Este diretório contém os testes para garantir a retrocompatibilidade comportamental dos CLIs após a refatoração da SAGA-017.

## Como Funciona

1.  **`generate_master.sh`**: Este script deve ser executado em um commit **anterior** à refatoração da Fase III. Ele executa os CLIs legados e salva sua saída nos arquivos `.golden`.
2.  **`test_golden_master.py`**: Este teste `pytest` executa os **mesmos** comandos no código-fonte **atual** (pós-refatoração) e compara a saída com o conteúdo dos arquivos `.golden`.

O teste falhará se houver qualquer diferença, garantindo que a "cirurgia" não alterou o comportamento externo.