from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .models import ChannelInput, AgentResponse, TriageResult, UrgencyLevel, PatientInfo
from .agent_processor import agent_processor
from .queue_manager import queue_manager
from .context_manager import context_manager
from .telemetry import telemetry
from .critical_keywords import detect_critical_keywords
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import uuid

# Security setup - simplified for mockup
SECRET_KEY = "nhs_digital_front_desk_mock_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Extended for easier testing

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Simple mock user database with predefined test users
fake_users_db = {
    "test-user-1": {
        "username": "demo_patient",
        "hashed_password": pwd_context.hash("password123"),
        "user_id": "test-user-1",
        "full_name": "Demo Patient",
        "email": "demo@example.com"
    },
    "test-user-2": {
        "username": "test_user",
        "hashed_password": pwd_context.hash("test123"),
        "user_id": "test-user-2",
        "full_name": "Test User",
        "email": "test@example.com"
    },
    "admin-user": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
        "user_id": "admin-user",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "is_admin": True
    }
}

app = FastAPI(
    title="Digital Front Desk & Triage Agent",
    description="AI-powered medical front desk system for patient triage and routing",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Authentication functions - simplified for mockup
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # For mockup purposes, we'll simplify token validation
        # In production, you would properly validate the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None or user_id not in fake_users_db:
            # For testing purposes, allow a fallback test user if token validation fails
            # This would be removed in production
            return {"user_id": "test-user-1"}
        
        return {"user_id": user_id}
    except jwt.PyJWTError:
        # For mockup testing, return a default test user instead of raising an exception
        # This ensures the API can be tested without a valid token
        # In production, you would properly handle this error
        return {"user_id": "test-user-1"}

# Authentication endpoints - simplified for mockup
@app.post("/register")
async def register_user(form_data: OAuth2PasswordRequestForm = Depends()):
    with telemetry.tracer.start_as_current_span("register_user") as span:
        # For mockup, check if username exists in any user
        username_exists = any(user["username"] == form_data.username for user in fake_users_db.values())
        if username_exists:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(form_data.password)
        
        user_data = {
            "username": form_data.username,
            "hashed_password": hashed_password,
            "user_id": user_id,
            "full_name": form_data.username,  # Mock data
            "email": f"{form_data.username}@example.com"  # Mock data
        }
        
        fake_users_db[user_id] = user_data
        
        # Create initial context for the user
        await context_manager.create_or_update_context(user_id, [], {})
        
        span.set_attributes({
            "user.id": user_id,
            "user.username": form_data.username
        })
        
        print(f"Mock registration successful: {form_data.username} (ID: {user_id})")
        return {"message": "User registered successfully", "user_id": user_id}

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with telemetry.tracer.start_as_current_span("login_user") as span:
        # For mockup purposes, find the user by username
        user = None
        for u in fake_users_db.values():
            if u["username"] == form_data.username:
                user = u
                break
        
        # For demo/testing, allow a special "auto login" username that doesn't require a password check
        if form_data.username == "auto_login":
            user = fake_users_db["test-user-1"]
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user["user_id"]}, expires_delta=access_token_expires
            )
            print(f"Mock auto-login successful: {user['username']} (ID: {user['user_id']})")
            return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}
        
        # Regular login check
        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["user_id"]}, expires_delta=access_token_expires
        )
        
        span.set_attributes({
            "user.id": user["user_id"],
            "user.username": user["username"]
        })
        
        print(f"Mock login successful: {user['username']} (ID: {user['user_id']})")
        return {"access_token": access_token, "token_type": "bearer", "user_id": user["user_id"]}

# For mockup testing - endpoint to get all users (would be removed in production)
@app.get("/debug/users")
async def get_all_users():
    """Debug endpoint to see all registered users - would be removed in production"""
    return [
        {
            "user_id": user_id,
            "username": user_data["username"],
            "full_name": user_data.get("full_name", ""),
            "email": user_data.get("email", "")
        } 
        for user_id, user_data in fake_users_db.items()
    ]

# Patient information endpoint - simplified for mockup
@app.post("/patient-info")
async def update_patient_info(patient_info: PatientInfo, current_user = Depends(get_current_user)):
    with telemetry.tracer.start_as_current_span("update_patient_info") as span:
        user_id = current_user["user_id"]
        
        # For mockup, we'll be more permissive with user ID mismatches
        if patient_info.user_id != user_id:
            print(f"User ID mismatch in patient info: {patient_info.user_id} vs {user_id}")
            patient_info.user_id = user_id  # Correct the ID for mockup
        
        # Update the context with patient info
        context = await context_manager.get_context(user_id)
        if not context:
            context = await context_manager.create_or_update_context(user_id, [])
        
        context.patient_info = patient_info
        await context_manager.create_or_update_context(
            user_id, 
            context.conversation_history, 
            context.metadata,
            patient_info
        )
        
        span.set_attributes({
            "user.id": user_id,
            "patient.age": patient_info.age or 0,
            "patient.sex": patient_info.sex or "unknown"
        })
        
        print(f"Mock patient info updated for: {user_id}")
        return {"message": "Patient information updated successfully"}

@app.post("/inquiries", response_model=Dict[str, Any])
async def process_inquiry(channel_input: ChannelInput, current_user = Depends(get_current_user)):
    """Process a new patient inquiry"""
    with telemetry.tracer.start_as_current_span("http_process_inquiry") as span:
        try:
            start_time = time.time()
            
            user_id = current_user["user_id"]
            if channel_input.user_id != user_id:
                raise HTTPException(status_code=400, detail="User ID mismatch")
            
            # Check for critical keywords
            critical_keywords = detect_critical_keywords(channel_input.message)
            
            try:
                # Try to process through agent
                agent_response, triage_result = await agent_processor.process_input(channel_input)
            except Exception as agent_error:
                # Fallback response if agent processing fails
                if critical_keywords:
                    # Create a basic response for critical conditions
                    triage_result = TriageResult(
                        urgency_level=UrgencyLevel.CRITICAL,
                        recommended_action="Immediate medical attention required",
                        reasoning="Critical keywords detected in message",
                        requires_human_attention=True
                    )
                    agent_response = AgentResponse(
                        response="I've detected potentially serious symptoms in your message. Please seek immediate medical attention or call emergency services.",
                        triage_score=1.0,
                        confidence_score=1.0,
                        suggested_actions=["Seek immediate medical attention", "Call emergency services"]
                    )
                else:
                    # Re-raise the error if no critical keywords
                    raise agent_error
            
            # If critical keywords were found, ensure high urgency
            if critical_keywords:
                triage_result.urgency_level = UrgencyLevel.CRITICAL
                triage_result.requires_human_attention = True
            
            # Record request processing time
            processing_time = (time.time() - start_time) * 1000
            telemetry.record_response_time(processing_time, "http_request")
            
            span.set_attributes({
                "http.status_code": 200,
                "http.processing_time_ms": processing_time,
                "critical_keywords_found": len(critical_keywords) > 0
            })
            
            return {
                "response": agent_response.response,
                "triage_result": {
                    "urgency_level": triage_result.urgency_level.name,
                    "recommended_action": triage_result.recommended_action,
                    "requires_human_attention": triage_result.requires_human_attention,
                    "critical_keywords_detected": critical_keywords if critical_keywords else []
                },
                "suggested_actions": agent_response.suggested_actions
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/queue/status")
async def get_queue_status():
    """Get current queue status"""
    with telemetry.tracer.start_as_current_span("http_queue_status") as span:
        try:
            status = queue_manager.get_queue_status()
            span.set_attributes({"http.status_code": 200})
            return status
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{user_id}")
async def get_user_context(user_id: str, current_user = Depends(get_current_user)):
    """Get the context for a user"""
    with telemetry.tracer.start_as_current_span("get_user_context") as span:
        try:
            # Verify the user is retrieving their own context
            if user_id != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
                
            context = await context_manager.get_context(user_id)
            
            if not context:
                raise HTTPException(status_code=404, detail="Context not found")
                
            span.set_attributes({
                "user.id": user_id,
                "context.history_length": len(context.conversation_history),
                "has_patient_info": context.patient_info is not None
            })
                
            return {
                "user_id": context.user_id,
                "last_updated": context.last_updated.isoformat(),
                "history_length": len(context.conversation_history),
                "patient_info": context.patient_info.dict() if context.patient_info else None
            }
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/queue/next")
async def get_next_queue_item():
    """Get the next item from the queue"""
    with telemetry.tracer.start_as_current_span("http_queue_next") as span:
        try:
            item = queue_manager.get_next_item()
            if item:
                span.set_attributes({
                    "http.status_code": 200,
                    "queue.item_found": True,
                    "queue.urgency_level": item.urgency_level.value
                })
                return {
                    "user_id": item.user_id,
                    "urgency_level": item.urgency_level.name,
                    "wait_time": (time.time() - item.timestamp.timestamp()),
                    "channel_type": item.channel_type,
                    "context_summary": item.context_summary
                }
            else:
                span.set_attributes({
                    "http.status_code": 404,
                    "queue.item_found": False
                })
                raise HTTPException(status_code=404, detail="No items in queue")
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/queue/{user_id}")
async def remove_from_queue(user_id: str):
    """Remove a user from the queue"""
    with telemetry.tracer.start_as_current_span("http_queue_remove") as span:
        try:
            queue_manager.remove_from_queue(user_id)
            span.set_attributes({
                "http.status_code": 200,
                "queue.user_id": user_id
            })
            return {"status": "success", "message": f"User {user_id} removed from queue"}
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(channel_input: ChannelInput):
    """Process a chat message"""
    with telemetry.tracer.start_as_current_span("http_chat") as span:
        try:
            start_time = time.time()
            
            # Process the input through our agent
            agent_response, _ = await agent_processor.process_input(channel_input)
            
            # Record request processing time
            processing_time = (time.time() - start_time) * 1000
            telemetry.record_response_time(processing_time, "chat_request")
            
            span.set_attributes({
                "http.status_code": 200,
                "http.processing_time_ms": processing_time
            })
            
            return {
                "response": agent_response.response
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise HTTPException(status_code=500, detail=str(e)) 