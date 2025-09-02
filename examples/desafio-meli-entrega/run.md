# Como Executar o Projeto

Este projeto é totalmente containerizado, então o único pré-requisito é ter o Docker e o Docker Compose instalados.

## Pré-requisitos
- Docker Engine
- Docker Compose

## Execução

1.  Clone este repositório para a sua máquina local.
2.  Navegue até o diretório raiz do projeto pelo seu terminal.
3.  Execute o script `run.sh` para construir a imagem e iniciar o container:
    ```sh
    ./run.sh
    ```

Após a execução, a API estará rodando em segundo plano.

- **URL da API:** [http://localhost:8000](http://localhost:8000)
- **Documentação Interativa (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

## Parando a Aplicação

Para parar o container, execute o seguinte comando no diretório raiz do projeto:

```sh
docker compose down
```

## Executando os Testes

Para executar os testes, você pode usar o `docker compose` para rodar o `pytest` dentro do container de serviço:

```sh
docker compose exec api pytest
```
