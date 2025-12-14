"""WebSocket endpoints for real-time chat."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.dependencies import get_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time chat with streaming responses.

    Args:
        websocket: WebSocket connection
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    chat_service = get_chat_service()

    try:
        while True:
            user_message = await websocket.receive_text()
            logger.info(f"Received message: {user_message}")

            if not user_message.strip():
                await websocket.send_text("Please provide a message.")
                continue

            try:
                async for chunk in chat_service.process_message(user_message):
                    await websocket.send_text(chunk)

                await websocket.send_text("[DONE]")

            except Exception as e:
                error_msg = f"Error processing message: {e}"
                logger.error(error_msg)
                await websocket.send_text(f"Error: {error_msg}")
                await websocket.send_text("[DONE]")

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass
