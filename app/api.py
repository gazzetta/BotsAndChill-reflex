import reflex as rx
from fastapi import FastAPI, Request, Response
from app.states.polar_state import PolarState

api = FastAPI()


@api.post("/api/polar/webhook")
async def handle_polar_webhook(request: Request):
    payload = await request.body()
    headers = dict(request.headers)
    result = await PolarState().handle_webhook(payload=payload, headers=headers)
    return Response(content=result["body"], status_code=result["status_code"])