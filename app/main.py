import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from app.config import SESSIONS_DIR, INTERVIEWER_PERSONA, DEFAULT_ROLE
from app.models import InterviewMode, SessionState, InterviewAnswer, InterviewQuestion
from app.services.interviewer import InterviewerBrain
from app.services.session import SessionManager
from app.services.voice import VoiceService

# Global state
active_sessions: dict[str, SessionState] = {}
interviewer = InterviewerBrain()
session_mgr = SessionManager(SESSIONS_DIR)
voice_service = VoiceService()

templates = Jinja2Templates(directory="app/templates")

class StartSessionRequest(BaseModel):
    job_description: str
    role_title: str = DEFAULT_ROLE
    mode: InterviewMode = InterviewMode.RECUITER_SCREEN
    duration_minutes: int = 20
    interviewer_style: str = INTERVIEWER_PERSONA
    use_voice: bool = True

class AnswerRequest(BaseModel):
    session_id: str
    answer_text: str

class RepeatDrillRequest(BaseModel):
    session_id: str
    question_index: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    yield

app = FastAPI(title="Blackwell Interview Flight Simulator", version="1.0.0", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", context={"request": request})

@app.post("/api/session/start")
async def start_session(req: StartSessionRequest):
    session_id = session_mgr.create_session_id()
    state = SessionState(
        job_description=req.job_description,
        role_title=req.role_title,
        mode=req.mode,
        interviewer_style=req.interviewer_style,
        duration_minutes=req.duration_minutes,
        is_active=True
    )
    # Generate first question
    question = await interviewer.generate_opening_question(
        req.job_description, req.mode, req.interviewer_style
    )
    state.questions.append(question)
    active_sessions[session_id] = state
    return {
        "session_id": session_id,
        "question": question.question,
        "mode": req.mode.value,
        "status": "active"
    }

@app.post("/api/session/answer")
async def submit_answer(req: AnswerRequest):
    state = active_sessions.get(req.session_id)
    if not state or not state.is_active:
        raise HTTPException(status_code=404, detail="Session not found or inactive")

    question = state.questions[state.current_question_index]
    score, followup = await interviewer.process_answer_and_followup(
        question.question, req.answer_text, state.job_description
    )

    answer = InterviewAnswer(
        transcript=req.answer_text,
        score=score,
        follow_up=followup
    )
    state.answers.append(answer)
    state.current_question_index += 1

    if followup:
        state.questions.append(InterviewQuestion(question=followup, mode=state.mode))

    return {
        "score": score.model_dump(),
        "follow_up": followup,
        "answers_given": len(state.answers),
        "questions_total": len(state.questions)
    }

@app.post("/api/session/repeat")
async def repeat_drill(req: RepeatDrillRequest):
    state = active_sessions.get(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    question = state.questions[req.question_index]
    return {
        "question": question.question,
        "repeat_prompt": f"Redo your answer to: {question.question}"
    }

@app.post("/api/session/end")
async def end_session(session_id: str):
    state = active_sessions.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state.is_active = False
    summary = session_mgr.save_session(session_id, state)
    del active_sessions[session_id]
    return summary

@app.get("/api/sessions")
async def list_sessions():
    return session_mgr.list_sessions()

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    session_dir = Path(SESSIONS_DIR) / session_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    transcript = (session_dir / "transcript.json").read_text()
    summary = (session_dir / "session_summary.md").read_text()
    return {"transcript": json.loads(transcript), "summary": summary}

@app.post("/api/voice/transcribe")
async def transcribe(audio_file: str):
    text = await voice_service.speech_to_text(audio_file)
    return {"text": text}

@app.post("/api/voice/speak")
async def speak(text: str):
    path = await voice_service.text_to_speech(text)
    if path:
        return FileResponse(path, media_type="audio/mpeg")
    return {"text": text}

@app.post("/api/practice/daily")
async def daily_practice(req: StartSessionRequest):
    """Start a daily practice session with 10 questions and 3 forced repeats."""
    session_id = session_mgr.create_session_id()
    state = SessionState(
        job_description=req.job_description,
        role_title=req.role_title,
        mode=req.mode,
        interviewer_style=req.interviewer_style,
        duration_minutes=req.duration_minutes,
        is_active=True
    )
    questions = await interviewer.generate_daily_practice_questions(
        req.job_description, 10, req.mode
    )
    state.questions = questions
    active_sessions[session_id] = state

    first_q = questions[0]
    return {
        "session_id": session_id,
        "question": first_q.question,
        "mode": req.mode.value,
        "total_questions": len(questions),
        "status": "daily_practice"
    }

# WebSocket endpoint for real-time interview
@app.websocket("/ws/interview/{session_id}")
async def interview_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    state = active_sessions.get(session_id)
    if not state:
        await websocket.close(4004, "Session not found")
        return

    try:
        while state.is_active:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "answer":
                question = state.questions[state.current_question_index]
                score, followup = await interviewer.process_answer_and_followup(
                    question.question, msg["text"], state.job_description
                )
                answer = InterviewAnswer(
                    transcript=msg["text"],
                    score=score,
                    follow_up=followup
                )
                state.answers.append(answer)
                state.current_question_index += 1
                if followup:
                    state.questions.append(InterviewQuestion(question=followup, mode=state.mode))

                await websocket.send_json({
                    "type": "score",
                    "score": score.model_dump(),
                    "follow_up": followup,
                    "answers_given": len(state.answers)
                })

            elif msg.get("type") == "end":
                state.is_active = False
                summary = session_mgr.save_session(session_id, state)
                await websocket.send_json({"type": "complete", "summary": summary})
                break

            elif msg.get("type") == "interruption":
                # Simulate interruption if candidate is rambling
                await websocket.send_json({
                    "type": "interruption",
                    "message": "Pause. Give me the short version."
                })
    except WebSocketDisconnect:
        state.is_active = False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
