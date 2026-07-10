FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system --no-cache torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt
RUN uv pip install --system --no-cache "git+https://github.com/ultralytics/CLIP.git"

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
