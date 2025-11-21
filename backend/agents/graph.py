from typing import Optional, Dict
import os
from dotenv import load_dotenv
from config import settings
import logging
from datetime import datetime, timedelta
from .react_agent import create_materials_agent
from langgraph.store.sqlite.aio import AsyncSqliteStore
from langgraph.checkpoint.memory import InMemorySaver  
import aiosqlite

from langfuse.langchain import CallbackHandler

load_dotenv()

logger = logging.getLogger(__name__)

_active_sessions: Dict[str, datetime] = {}

def get_langfuse_handler() -> Optional[CallbackHandler]:
    """Initialize Langfuse callback handler if enabled"""
    if settings.ENABLE_LANGFUSE and settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
        return CallbackHandler(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST
        )
    return None

_agent_executor = None
_checkpointer_context = None
_store_context = None
_checkpointer = None

async def cleanup_old_sessions(checkpointer: InMemorySaver, is_new_session: bool = False):
    """
    Clean up old/inactive sessions from InMemorySaver to free RAM.
    
    Args:
        checkpointer: The InMemorySaver instance
        is_new_session: If True, this is a new session (orphaned old one)
    """
    global _active_sessions
    
    if not checkpointer:
        return
    
    now = datetime.now()
    inactive_threshold = timedelta(minutes=settings.SESSION_CLEANUP_INACTIVE_MINUTES)
    cleaned_count = 0
    
    sessions_to_remove = []
    for session_id, last_access in list(_active_sessions.items()):
        if now - last_access > inactive_threshold:
            sessions_to_remove.append(session_id)

    if is_new_session and settings.SESSION_CLEANUP_ON_NEW_SESSION:
        for session_id, last_access in list(_active_sessions.items()):
            if now - last_access > timedelta(minutes=5):
                if session_id not in sessions_to_remove:
                    sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        try:
            if hasattr(checkpointer, '_storage'):
                if session_id in checkpointer._storage:
                    del checkpointer._storage[session_id]
                    cleaned_count += 1
                    logger.debug(f"Cleaned up session {session_id[:8]}... from memory")
            elif hasattr(checkpointer, 'storage'):
                if session_id in checkpointer.storage:
                    del checkpointer.storage[session_id]
                    cleaned_count += 1
            else:
                logger.debug(f"Cannot access InMemorySaver storage to clean session {session_id[:8]}...")
        except Exception as e:
            logger.warning(f"Failed to clean up session {session_id[:8]}...: {e}")
        
        _active_sessions.pop(session_id, None)
    
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} inactive session(s) from memory")

def get_checkpointer():
    """Get the checkpointer instance for cleanup operations"""
    global _checkpointer
    return _checkpointer

async def get_agent():
    """Get or create the agent instance with memory"""
    global _agent_executor, _checkpointer_context, _store_context, _checkpointer
    
    if _agent_executor is None:
        _checkpointer = InMemorySaver()  
        logger.info("Short-term memory (checkpointer) initialized")
     
        _store_context = AsyncSqliteStore.from_conn_string("long_term_memory.db")
        store = await _store_context.__aenter__()
        logger.info("Long-term memory (store) initialized")
        
        _agent_executor = create_materials_agent(checkpointer=_checkpointer, store=store)
        logger.info("ReAct agent initialized with memory")
    
    return _agent_executor

async def run_agent(user_query: str, session_id: str, is_new_session: bool = False):
    """
    Run the ReAct agent with a user query
    
    Short-term memory (checkpointer): Stores conversation history per session
    Long-term memory (store): Stores user facts/preferences across sessions
    
    Args:
        user_query: The user's message
        session_id: Session identifier (thread_id)
        is_new_session: True if this is a new session (for cleanup of orphaned sessions)
    """
    global _active_sessions, _checkpointer
    
    logger.info(f"Starting ReAct agent for session {session_id[:8]}...")
    logger.info(f"Query: {user_query[:100]}...")
    
    _active_sessions[session_id] = datetime.now()
    
    if is_new_session and _checkpointer:
        await cleanup_old_sessions(_checkpointer, is_new_session=True)
    
    agent = await get_agent()
    
    config = {
        "configurable": {
            "thread_id": session_id,
            "user_id": session_id
        }
    }
    
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]
        logger.info("Langfuse observability enabled")
    
    result = await agent.ainvoke(
        {"messages": [("user", user_query)]},
        config=config
    )
    
    logger.info(f"ReAct agent completed successfully!")
    
    final_message = result["messages"][-1].content if result.get("messages") else ""
    
    # Extract images from tool calls in THIS turn only (not from conversation history)
    # We look backwards from the final message to find tool calls from this turn
    images = []
    all_messages = result.get("messages", [])
    
    last_user_idx = -1
    for i in range(len(all_messages) - 1, -1, -1):
        msg = all_messages[i]
        if hasattr(msg, "type") and msg.type == "human":
            last_user_idx = i
            break
    
    if last_user_idx >= 0:
        for msg in all_messages[last_user_idx:]:
            if hasattr(msg, "type") and msg.type == "tool":
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    try:
                        import json
                        tool_result = json.loads(msg.content)
                        if isinstance(tool_result, dict) and tool_result.get("type") == "image":
                            images.append({
                                "smiles": tool_result.get("smiles"),
                                "image_data": tool_result.get("image_url_format"),
                                "width": tool_result.get("width"),
                                "height": tool_result.get("height")
                            })
                    except:
                        pass
    
    return {
        "final_response": final_message,
        "reasoning_trace": [],
        "search_results": {},
        "conversation_history": [],
        "images": images
    }
