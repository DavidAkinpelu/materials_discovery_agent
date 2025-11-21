from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
from agents.graph import run_agent, get_agent
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
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Received chat request - Session: {session_id[:8]}... Query: {request.message[:100]}...")
        
        # Run agent (state is managed by LangGraph checkpointer)
        logger.info(f"Starting agent execution...")
        result = await run_agent(
            user_query=request.message,
            session_id=session_id
        )
        
        logger.info(f"Agent completed successfully - Response length: {len(result.get('final_response', ''))} chars")
        logger.info('final_response: ' + result['final_response'])
        
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
        
        # Format for frontend if necessary (frontend expects query/response/timestamp)
        # Our node saves it exactly in that format.
        
        # Sort by timestamp desc (newest first) as per previous implementation
        # But node appends, so list is old -> new.
        # Frontend expects:
        # "for c in reversed(convs)" -> implies it returns newest first?
        # Previous implementation: order_by(desc).all() -> newest first.
        # But then `for c in reversed(convs)` -> makes it oldest first?
        # Let's check the frontend code to be sure.
        # Frontend just maps it.
        # Let's return it as is (oldest -> newest) and let frontend handle display, 
        # OR match the previous behavior.
        # Previous behavior: `return [ ... for c in reversed(convs) ]` where convs was DESC (newest first).
        # So `reversed(convs)` made it ASC (oldest first).
        # Our list is already ASC. So we just return it.
        
        return {"history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
