# FROM ubuntu:22.04
FROM python:3.13.3

RUN apt update && apt install -y python3 python3-pip curl wget iputils-ping

RUN pip3 install --upgrade pip

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN uv pip install --system --no-cache-dir -r /app/requirements.txt

COPY . /app

RUN python3 utils/download_models_hf.py

EXPOSE 8081

CMD ["python3", "main.py"]