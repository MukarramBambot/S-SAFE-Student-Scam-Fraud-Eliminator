import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Header, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from backend.core import run_full_analysis
from backend.database import db
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_user_from_token
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

app = FastAPI(title="S-SAFE AI", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# ===== PYDANTIC MODELS =====

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class AnalyzeRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None

class NewChatRequest(BaseModel):
    title: Optional[str] = "New Chat"

# ===== AUTHENTICATION DEPENDENCY =====

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Dependency to get current user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Extract token from "Bearer <token>"
        token = authorization.replace("Bearer ", "")
        user_data = get_user_from_token(token)
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Verify user exists in database
        user = db.get_user_by_id(user_data["user_id"])
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# ===== ROUTES =====

@app.get("/")
async def read_index():
    return FileResponse(FRONTEND_DIR / "index.html")

# ===== AUTHENTICATION ENDPOINTS =====

@app.post("/register")
async def register(request: RegisterRequest):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = db.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        existing_email = db.get_user_by_email(request.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate password length
        if len(request.password) > 128:
            raise HTTPException(status_code=400, detail="Password cannot be longer than 128 characters")
        
        # Hash password and create user
        password_hash = hash_password(request.password)
        user_id = db.create_user(request.username, request.email, password_hash)
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Create access token
        token = create_access_token({"user_id": user_id, "username": request.username})
        
        logger.info(f"New user registered: {request.username}")
        
        return {
            "message": "User created successfully",
            "token": token,
            "user": {
                "id": user_id,
                "username": request.username,
                "email": request.email
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    try:
        # Get user from database
        user = db.get_user_by_username(request.username)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Verify password
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        token = create_access_token({"user_id": user["id"], "username": user["username"]})
        
        logger.info(f"User logged in: {request.username}")
        
        return {
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "created_at": current_user["created_at"]
    }

# ===== CHAT MANAGEMENT ENDPOINTS =====

@app.post("/new_chat")
async def create_new_chat(
    request: NewChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat session."""
    try:
        chat_id = db.create_chat(current_user["id"], request.title)
        
        if not chat_id:
            raise HTTPException(status_code=500, detail="Failed to create chat")
        
        logger.info(f"New chat created: {chat_id} for user {current_user['username']}")
        
        return {
            "chat_id": chat_id,
            "title": request.title,
            "message": "Chat created successfully"
        }
    except Exception as e:
        logger.exception("Failed to create chat")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats")
async def get_user_chats(current_user: dict = Depends(get_current_user)):
    """Get all chats for the current user."""
    try:
        chats = db.get_user_chats(current_user["id"])
        return {"chats": chats}
    except Exception as e:
        logger.exception("Failed to get chats")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get all messages for a specific chat."""
    try:
        # Verify chat belongs to user
        chat = db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        if chat["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        messages = db.get_chat_messages(chat_id)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get messages")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a chat and all its messages."""
    try:
        # Verify chat belongs to user
        chat = db.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        if chat["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        db.delete_chat(chat_id)
        logger.info(f"Chat deleted: {chat_id}")
        
        return {"message": "Chat deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete chat")
        raise HTTPException(status_code=500, detail=str(e))

# ===== ANALYSIS ENDPOINTS (Updated) =====

@app.post("/analyze")
async def analyze_text(
    request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Analyze text and save to chat history."""
    try:
        text = request.message
        chat_id = request.chat_id
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # If no chat_id provided, create a new chat
        if not chat_id:
            # Generate title from first few words
            title = text[:50] + "..." if len(text) > 50 else text
            chat_id = db.create_chat(current_user["id"], title)
        
        # Verify chat belongs to user
        chat = db.get_chat(chat_id)
        if not chat or chat["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Save user message
        db.save_message(chat_id, "user", text)
        
        # Run analysis
        logger.info(f"Analyzing text for user {current_user['username']}: {text[:50]}...")
        result = run_full_analysis(text)
        
        # Save agent response
        response_content = result.get("decision", {}).get("explanation", "Analysis complete.")
        db.save_message(chat_id, "agent", response_content, result)
        
        # Update chat title if it's the first message
        messages = db.get_chat_messages(chat_id)
        if len(messages) <= 2:  # First exchange
            title = text[:50] + "..." if len(text) > 50 else text
            db.update_chat_title(chat_id, title)
        
        return format_response(result, chat_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Analysis failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze_file")
async def analyze_file(
    message: str = "",
    files: List[UploadFile] = File(...),
    chat_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Analyze uploaded files."""
    try:
        file_summaries = []
        total_content = message + "\n\n[Extracted File Content]:\n"
        
        for file in files:
            content = await file.read()
            
            # Extract text from file
            from backend.tools.file_extractor import extract_text
            extracted = extract_text(content, file.filename)
            
            file_summaries.append(file.filename)
            total_content += f"\n--- File: {file.filename} ---\n{extracted}\n-------------------\n"
            
            # Save to DB
            db.save_uploaded_file(file.filename, file.content_type, f"memory://{file.filename}")
        
        # If no chat_id, create new chat
        if not chat_id:
            title = f"File Analysis: {', '.join(file_summaries)}"
            chat_id = db.create_chat(current_user["id"], title)
        
        # Save user message
        db.save_message(chat_id, "user", f"Uploaded files: {', '.join(file_summaries)}")
        
        # Run analysis
        logger.info(f"Analyzing files: {file_summaries}")
        result = run_full_analysis(total_content)
        
        # Save agent response
        response_content = result.get("decision", {}).get("explanation", "Analysis complete.")
        db.save_message(chat_id, "agent", response_content, result)
        
        return format_response(result, chat_id)
    except Exception as e:
        logger.exception("File analysis failed")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/save_toon")
async def save_toon(request: Request, current_user: dict = Depends(get_current_user)):
    """Update TOON patterns (admin only for now)."""
    try:
        data = await request.json()
        file_type = data.get("file_type")  # "scam" or "positive"
        key = data.get("key")
        value = data.get("value")
        
        if not all([file_type, key, value]):
            raise HTTPException(status_code=400, detail="Missing fields")
        
        from backend.toon import toon_manager
        toon_manager.update_pattern(file_type, key, value)
        
        logger.info(f"Updated TOON via API: {key} -> {value}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"TOON update failed: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

def format_response(result: Dict[str, Any], chat_id: Optional[int] = None) -> Dict[str, Any]:
    """Format analysis response for frontend."""
    decision = result.get("decision", {})
    extraction = result.get("extraction", {})
    research = result.get("research", {})
    
    response = {
        "result": decision.get("result", "Needs Verification"),
        "explanation": decision.get("explanation", "Analysis complete."),
        "decision": decision,
        "extraction": extraction,
        "research": research,
        "chat_id": chat_id
    }
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
