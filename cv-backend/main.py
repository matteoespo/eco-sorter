import base64
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import requests
import json
import os
import time
from ultralytics import YOLOWorld

app = FastAPI()

# Load YOLO-World open-vocabulary model — detects ANY object you define
model = YOLOWorld('yolov8s-world.pt')

# Define comprehensive eco-sorting categories
# YOLO-World can detect anything described in natural language
ECO_CLASSES = [
    # Recyclables
    "plastic bottle", "glass bottle", "aluminum can", "tin can", "cardboard box",
    "paper", "newspaper", "magazine", "envelope", "plastic bag", "plastic container",
    "glass jar", "milk carton", "juice box", "cereal box", "pizza box",
    # Electronics / E-Waste
    "cell phone", "smartphone", "laptop", "tablet", "keyboard", "computer mouse",
    "headphones", "earbuds", "charger", "USB cable", "power cable", "remote control",
    "battery", "vape", "e-cigarette", "light bulb", "LED bulb",
    # Organic / Compost
    "banana", "apple", "orange", "food scraps", "bread", "egg shell",
    "coffee cup", "tea bag", "fruit", "vegetable",
    # Hazardous
    "paint can", "spray can", "aerosol can", "medicine bottle", "syringe",
    "cleaning product", "chemical bottle", "motor oil bottle",
    # General Household
    "cup", "mug", "plate", "bowl", "fork", "knife", "spoon",
    "water bottle", "wine glass", "straw", "napkin", "tissue",
    "toothbrush", "pen", "pencil", "scissors", "tape",
    "shoe", "clothing", "t-shirt", "sock", "towel", "diaper",
    "toy", "stuffed animal", "book", "backpack", "handbag",
]

model.set_classes(ECO_CLASSES)

LLM_URL = os.getenv("LLM_URL", "http://llm-backend:11434/api/generate")

class DetectionState:
    def __init__(self):
        self.current_label = None
        self.first_detected_time = 0
        self.last_llm_response = None

state = DetectionState()

def analyze_with_llm(label):
    prompt = f"""
    You are an eco-sorting assistant. The user has presented a '{label}'.
    Please provide the recycling category, action required, and a fun fact.
    Respond ONLY with valid JSON matching this schema exactly:
    {{
      "item": "{label}",
      "category": "Recycling | Trash | Compost | Hazardous",
      "action_required": "Brief instruction",
      "fun_fact": "A short interesting fact"
    }}
    """
    try:
        response = requests.post(LLM_URL, json={
            "model": "gemma:2b",
            "prompt": prompt,
            "format": "json",
            "stream": False
        }, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return json.loads(data.get('response', '{}'))
    except Exception as e:
        print(f"LLM Error: {e}")
    return None

@app.websocket("/process-frame")
async def process_frame(websocket: WebSocket):
    await websocket.accept()
    global state
    try:
        while True:
            data = await websocket.receive_text()
            # data is base64 encoded image
            if "," in data:
                encoded_data = data.split(',')[1]
            else:
                encoded_data = data
            
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                await websocket.send_json({"error": "Failed to decode image"})
                continue
                
            # Run YOLO-World inference
            img_h, img_w = img.shape[:2]
            results = model(img, stream=False, verbose=False, conf=0.3)
            
            best_det = None
            best_conf = 0.0
            detections = []
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    # xyxy bounding box normalized to 0-1
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append({
                        "label": label,
                        "confidence": round(conf, 3),
                        "bbox": [
                            round(x1 / img_w, 4),
                            round(y1 / img_h, 4),
                            round(x2 / img_w, 4),
                            round(y2 / img_h, 4),
                        ]
                    })
                    if conf > best_conf:
                        best_conf = conf
                        best_det = label
            
            current_time = time.time()
            response_payload = {
                "detected": best_det,
                "confidence": best_conf,
                "detections": detections,
                "llm_result": None
            }
            
            if best_det and best_conf > 0.3:
                if state.current_label != best_det:
                    state.current_label = best_det
                    state.first_detected_time = current_time
                    state.last_llm_response = None
                else:
                    if (current_time - state.first_detected_time) > 1.5 and not state.last_llm_response:
                        # Debounce logic passed, call LLM
                        llm_res = analyze_with_llm(best_det)
                        state.last_llm_response = llm_res
                
                response_payload["llm_result"] = state.last_llm_response
            else:
                state.current_label = None
                
            await websocket.send_json(response_payload)
            
    except WebSocketDisconnect:
        print("Client disconnected")
