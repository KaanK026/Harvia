# python
import json
import uuid
from fastapi import APIRouter, Request, HTTPException
from starlette import status
from starlette.responses import JSONResponse, StreamingResponse

from backend.LLM.qa import chat, chat_stream, clear_session, get_session_history
from backend.src.models.request_models import QuestionRequest, ClearSessionRequest
from backend.src.services.llm import get_llm_components
from backend.src.utils.logger import get_logger

router = APIRouter()
logger = get_logger('chat')

faiss_index = None
qa_chain = None
qa_chain_streaming = None

def _load_components():
    global faiss_index, qa_chain, qa_chain_streaming
    try:
        components = get_llm_components()
        faiss_index = components.get("faiss_index")
        qa_chain = components.get("qa_chain")
        qa_chain_streaming = components.get("qa_chain_streaming")
        logger.info(
            f"LLM components loaded (faiss_index is None? {faiss_index is None}, "
            f"faiss_size={getattr(faiss_index, 'ntotal', 'n/a')})"
        )
    except Exception as e:
        logger.error(f"Error loading LLM components: {e}", exc_info=True)

# Initial load (will run on import; safe if reloader triggers multiple times)
_load_components()

def _ensure_components():
    # Lazy reload if something came up None (e.g. due to import order with reloader)
    if faiss_index is None or qa_chain is None or qa_chain_streaming is None:
        logger.warning("Components missing; attempting reload.")
        _load_components()

@router.post("/ask")
async def ask_endpoint(request: QuestionRequest):
    _ensure_components()

    if faiss_index is None:
        logger.error("FAISS index is not loaded (None).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service unavailable. FAISS index not loaded."
        )

    if qa_chain is None:
        logger.error("QA chain is not initialized (None).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service unavailable. QA chain not initialized."
        )

    # Optional: allow empty index but warn
    if getattr(faiss_index, "ntotal", 1) == 0:
        logger.warning("FAISS index loaded but empty (ntotal=0). Proceeding with fallback responses.")

    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Processing question for session_id={session_id}")

    try:
        response = chat(qa_chain, request.question, session_id=session_id)
        if response is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process question"
            )
        if isinstance(response, dict):
            response["session_id"] = session_id
        return JSONResponse(content=response, headers={"X-Session-Id": session_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing question"
        )

@router.post("/ask-stream")
async def ask_stream_endpoint(request: QuestionRequest):
    _ensure_components()

    if faiss_index is None:
        logger.error("FAISS index is not loaded (None).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service initializing. Please try again."
        )

    if qa_chain_streaming is None:
        logger.error("QA chain streaming not initialized (None).")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service initializing. Please try again."
        )

    if getattr(faiss_index, "ntotal", 1) == 0:
        logger.warning("FAISS index loaded but empty (ntotal=0). Streaming may return low-quality results.")

    session_id = request.session_id or str(uuid.uuid4())
    logger.info(f"Starting stream for session_id={session_id}")

    async def generate_stream():
        try:
            yield f"data: {json.dumps({'type': 'session_init', 'session_id': session_id})}\n\n"
            async for chunk in chat_stream(qa_chain_streaming, request.question, session_id=session_id):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id})}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Error processing question', 'session_id': session_id})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Session-Id": session_id,
            "Access-Control-Expose-Headers": "X-Session-Id"
        }
    )

@router.post("/clear-session")
async def clear_session_endpoint(request: ClearSessionRequest):
    try:
        success = clear_session(request.session_id)
        if success:
            return {"success": True, "message": "Session cleared successfully", "session_id": request.session_id}
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "error": "Session not found", "session_id": request.session_id}
        )
    except Exception as e:
        logger.error(f"Error clearing session: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error clearing session")

@router.get("/session/{session_id}/history")
async def get_session_history_endpoint(session_id: str):
    try:
        history = get_session_history(session_id)
        if history:
            return {
                "success": True,
                "session_id": session_id,
                "history": history.messages if hasattr(history, 'messages') else []
            }
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "error": "Session not found", "session_id": session_id}
        )
    except Exception as e:
        logger.error(f"Error getting session history: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting session history")
