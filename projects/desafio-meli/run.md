# How to Run the Project

This project is fully containerized, so the only prerequisite is having Docker and Docker Compose installed.

## Prerequisites
- Docker Engine
- Docker Compose

## Execution

1.  Clone this repository to your local machine.
2.  Navigate to the project's root directory in your terminal.
3.  Execute the `run.sh` script to build the image and start the container:
    ```sh
    ./run.sh
    ```

After execution, the API will be running in the background.

- **API URL:** [http://localhost:8000](http://localhost:8000)
- **Interactive Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

## Stopping the Application

To stop the container, execute the following command in the project's root directory:

```sh
docker compose down
```

## Running the Tests

To run the tests, you can use `docker compose` to run `pytest` inside the service container:

```sh
docker compose exec api pytest
```