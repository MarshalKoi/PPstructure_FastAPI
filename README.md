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

## Need more details?
You can read my thesis paper for the long version and the presentation for the short version
- [Thesis Document](https://docs.google.com/document/d/178FzHWxzerKCBOjJgcZAgVI7kRnzq_IA/edit?usp=sharing&ouid=109944872417369808585&rtpof=true&sd=true)  
- [Presentation Slides](https://docs.google.com/presentation/d/1_VoUx-1V7uMP2rEbMVtSqa2pv4guORb_WIldkMVsrfU/edit?usp=sharing)  
