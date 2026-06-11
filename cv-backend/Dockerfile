FROM python:3.11-slim

# Install system dependencies required by opencv + git for CLIP
RUN apt-get update && apt-get install -y git libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system --no-cache torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN uv pip install --system --no-cache -r requirements.txt
RUN uv pip install --system --no-cache "git+https://github.com/ultralytics/CLIP.git"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
