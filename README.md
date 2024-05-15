# PPstructure_FastAPI
A simple way to deploy `PPstructure` from `PaddleOCR` using `FastAPI`, `Docker`, `Uvicorn`

## Deployment Method
Use Docker to deploy the service.
1. clone the repository

    ```shell
    git clone https://github.com/littleNightK/PPstructure_FastAPI.git
    ```
2. build the docker image
    ```shell
    docker build -t ppstructurefastapi:latest .
    ```

3. Create the Docker container and run
    ```shell
    docker compose up -d
    ```
5. Swagger Page at `localhost:8000/docs`