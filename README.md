# 🌱 Eco-Sorter

Real-time AI-powered waste sorting assistant using computer vision and a large language model. Point your webcam at an object and Eco-Sorter will identify it, classify it into the correct disposal category, and provide recycling guidance with fun facts.

---

## Architecture

```
┌──────────────┐        WebSocket (base64 frames)         ┌──────────────────┐
│              │ ──────────────────────────────────────▶   │                  │
│   Frontend   │                                          │   CV Backend     │
│  (Next.js)   │ ◀──────────────────────────────────────  │  (FastAPI +      │
│  :3000       │   JSON { detections, llm_result }        │   YOLO-World)    │
└──────────────┘                                          │  :8000           │
                                                          └────────┬─────────┘
                                                                   │
                                                          httpx POST (async)
                                                                   │
                                                          ┌────────▼─────────┐
                                                          │                  │
                                                          │   LLM Backend    │
                                                          │  (Ollama +       │
                                                          │   Gemma 2B)      │
                                                          │  :11434          │
                                                          └──────────────────┘
```

## Services

| Service | Technology | Purpose | Port |
|---------|-----------|---------|------|
| **frontend** | Next.js (React) | Webcam streaming UI, displays detections and LLM guidance | `3000` |
| **cv-backend** | FastAPI + YOLO-World XL | WebSocket frame processing, object detection with per-class thresholds | `8000` |
| **llm-backend** | Ollama + Gemma 2B | Item classification, disposal advice, and fun facts via JSON API | `11434` |

## Quick Start

```bash
# Clone and build
git clone <repo-url> eco-sorter
cd eco-sorter

# Start all services
docker compose up --build

# Open the app
open http://localhost:3000
```

> **Note:** The first run will download the YOLO-World XL model (~400 MB) and the Gemma 2B LLM (~1.5 GB). Subsequent runs use cached volumes.

## Environment Variables

All configurable via `docker-compose.yml` → `cv-backend` → `environment`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_URL` | `http://llm-backend:11434/api/generate` | Ollama API endpoint |
| `LLM_MODEL` | `gemma:2b` | LLM model name to use |
| `LLM_TIMEOUT` | `15.0` | HTTP timeout for LLM requests (seconds) |
| `YOLO_MODEL_NAME` | `yolov8x-world.pt` | YOLO-World model weights file |
| `YOLO_WEIGHTS_DIR` | `/app/weights` | Directory for cached model weights |
| `DEFAULT_CONFIDENCE` | `0.20` | Fallback detection confidence threshold |
| `DEBOUNCE_SECONDS` | `1.5` | Seconds to wait before querying the LLM |
| `LOG_LEVEL` | `INFO` | Application log level |

## Project Structure

```
eco-sorter/
├── services/
│   ├── cv-backend/
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI entrypoint with lifespan hooks
│   │   │   ├── core/
│   │   │   │   ├── config.py         # Settings, eco-classes, thresholds, category map
│   │   │   │   └── logging.py        # Structured logging setup
│   │   │   ├── models/
│   │   │   │   └── schemas.py        # Pydantic request/response models
│   │   │   ├── api/
│   │   │   │   ├── router.py         # Master API router
│   │   │   │   └── endpoints/
│   │   │   │       └── process.py    # WebSocket /process-frame endpoint
│   │   │   └── services/
│   │   │       ├── detector.py       # YOLO-World detection wrapper
│   │   │       └── llm.py           # Async Ollama client (httpx)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── weights/                  # Cached model weights (Docker volume)
│   ├── frontend/                     # Next.js webcam UI
│   └── llm-backend/
│       └── entrypoint.sh            # Ollama server startup + model pull
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Key Design Decisions

### Class-Specific Confidence Thresholds
Instead of a single global threshold, each eco-class has its own confidence floor. High-contrast objects (e.g. `plastic bottle` at `0.15`) use lower thresholds for maximum recall, while ambiguous categories (e.g. `electronic device` at `0.25`) use higher thresholds for precision.

### Optimised Class Vocabulary
The original 60+ fine-grained classes caused semantic dilution in YOLO-World's open-vocabulary head. The refactored vocabulary uses ~31 broader, human-recognisable categories that map cleanly to 4 disposal groups: **Recyclable**, **Trash**, **Compost**, and **Hazardous**.

### Async Architecture
The LLM client uses `httpx.AsyncClient` instead of `requests`, preventing frame-processing from blocking during slow LLM generation. The YOLO model inference runs with a `threading.Lock` for thread safety under uvicorn's async workers.

### Debounce Logic
The LLM is only queried after an object has been stably detected for a configurable period (default 1.5s), preventing excessive API calls during rapid scene changes.

## Tech Stack

- **[YOLO-World](https://github.com/AILab-CVC/YOLO-World)** (XL variant) — open-vocabulary object detection
- **[FastAPI](https://fastapi.tiangolo.com/)** — async WebSocket and REST API
- **[Next.js](https://nextjs.org/)** — React-based webcam streaming frontend
- **[Ollama](https://ollama.ai/)** — local LLM inference server
- **[Gemma 2B](https://ai.google.dev/gemma)** — compact LLM for classification + text generation
- **[httpx](https://www.python-httpx.org/)** — async HTTP client
- **[Pydantic](https://docs.pydantic.dev/)** — data validation and settings management

## License

MIT
