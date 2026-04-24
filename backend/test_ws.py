"""纯 FastAPI 测试 WebSocket"""
import uvicorn
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("connected")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
