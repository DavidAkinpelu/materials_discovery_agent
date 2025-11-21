from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from agents.graph import run_agent, get_agent, cleanup_old_sessions, get_checkpointer
from models.schemas import ChatRequest, ChatResponse
import uuid
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Materials Discovery Agent API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:5000",
        "http://localhost:5001",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["*"],
    max_age=3600,
)

@app.get("/")
async def root():
    return {
        "message": "Materials Discovery Agent API",
        "version": "1.0"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        is_new_session = request.session_id is None
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Received chat request")
        
        logger.info(f"Starting agent execution...")
        result = await run_agent(
            user_query=request.message,
            session_id=session_id,
            is_new_session=is_new_session
        )
        
        logger.info(f"Agent completed successfully")
        
        return ChatResponse(
            response=result['final_response'],
            reasoning_trace=result['reasoning_trace'],
            search_results=result['search_results'],
            session_id=session_id,
            images=result.get('images', [])
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        logger.error(f"ERROR in chat endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history from LangGraph state"""
    try:
        agent = await get_agent()
        config = {"configurable": {"thread_id": session_id}}
        state_snapshot = await agent.aget_state(config)
        
        if not state_snapshot.values:
            return {"history": []}
            
        history = state_snapshot.values.get("conversation_history", [])
        
        return {"history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cleanup-sessions")
async def cleanup_sessions():
    """Manually trigger cleanup of old/inactive sessions from memory"""
    try:
        checkpointer = get_checkpointer()
        if not checkpointer:
            return {"message": "No checkpointer available", "cleaned": 0}
        
        await cleanup_old_sessions(checkpointer, is_new_session=False)
        return {"message": "Cleanup completed", "status": "success"}
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
