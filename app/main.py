"""Blackwell Interview Flight Simulator — FastAPI backend.

Routes:
  GET /              — serve browser UI
  POST /api/start    — create session, return first question
  POST /api/answer   — submit answer, get score + follow-up
  POST /api/repeat   — retry the same question
  GET  /api/sessions — list all saved sessions
  DELETE /api/session/{id} — delete a session
  GET  /api/session/{id}   — get session state
"""
import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.config import SESSIONS_DIR, LLM_BASE_URL
from app.models import (
    InterviewMode, SessionState, InterviewAnswer, InterviewQuestion,
    StartSessionRequest, AnswerRequest, RepeatDrillRequest, AnswerScore,
    ScoringCriteria,
)
from app.services.interviewer import InterviewerBrain
from app.services.session import SessionManager

logger = logging.getLogger(__name__)

# ── Error contract ─────────────────────────────────────────────────────


def error_response(message: str, error_type: str = "error", path: str = "") -> JSONResponse:
    """Standardized JSON error response."""
    return JSONResponse(
        status_code=400,
        content={
            "ok": False,
            "error": message,
            "type": error_type,
            "path": path,
        },
    )


# ── App setup ──────────────────────────────────────────────────────────

active_sessions: dict[str, SessionState] = {}
interviewer = InterviewerBrain()
session_mgr = SessionManager(SESSIONS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Blackwell Interview Flight Simulator",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Static files ────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    """Serve the browser UI."""
    return FileResponse(
        os.path.join(STATIC_DIR, "index.html"),
        media_type="text/html"
    )


# ── Interview lifecycle ────────────────────────────────────────────────

@app.post("/api/start")
async def start_session(req: StartSessionRequest):
    """Start a new interview session. Returns first question."""
    try:
        session_id = session_mgr.create_session_id()
        state = SessionState(
            session_id=session_id,
            job_description=req.job_description,
            role_title=req.role_title,
            mode=req.mode,
            interviewer_style=req.interviewer_style,
            duration_minutes=req.duration_minutes,
            is_active=True,
        )

        try:
            question = await interviewer.generate_opening_question(
                req.job_description, req.mode, req.interviewer_style
            )
        except Exception as e:
            logger.error("LLM failed to generate opening question: %s", e)
            question = InterviewQuestion(
                question="Walk me through your background and why this role makes sense.",
                mode=req.mode,
            )

        state.questions.append(question)
        active_sessions[session_id] = state

        return {
            "session_id": session_id,
            "question": question.question,
            "mode": req.mode.value,
            "status": "active",
        }
    except Exception as e:
        logger.exception("Failed to start session")
        return error_response(str(e), "start_failed", "/api/start")


@app.post("/api/answer")
async def submit_answer(req: AnswerRequest):
    """Submit an answer. Returns score + follow-up question or retry request."""
    state = active_sessions.get(req.session_id)
    if not state:
        return JSONResponse(status_code=404, content={"ok": False, "error": "Session not found"})

    try:
        if state.current_question_index >= len(state.questions):
            return JSONResponse(status_code=400, content={
                "ok": False,
                "error": "All questions completed. Call /api/start to begin a new session.",
            })
        current_q = state.questions[state.current_question_index]

        # Track retry identity
        prev_answers_for_q = [
            a for a in state.answers
            if not a.is_retry or a.question_index == state.current_question_index
        ]
        attempt_number = len(prev_answers_for_q) + 1
        is_retry = attempt_number > 1

        try:
            score, followup = await interviewer.process_answer_and_followup(
                current_q.question, req.answer_text, state.job_description
            )
        except Exception as e:
            logger.error("LLM scoring failed: %s", e)
            score, followup = _fallback_score(req.answer_text, current_q.question)

        answer = InterviewAnswer(
            transcript=req.answer_text,
            score=score,
            question_index=state.current_question_index,
            attempt_number=attempt_number,
            is_retry=is_retry,
            follow_up=followup if score.overall < 6 else None,
        )
        state.answers.append(answer)

        result: dict = {
            "score": score.model_dump(),
            "needs_retry": score.overall < 6,
        }

        if score.overall >= 6:
            state.current_question_index += 1
            
            # Generate a new follow-on question for the next round
            try:
                next_q_text = await interviewer._generate_next_question(
                    state.job_description, state.mode, state.interviewer_style,
                    state.current_question_index, state.answers
                )
                new_q = InterviewQuestion(question=next_q_text, mode=state.mode)
                state.questions.append(new_q)
                result["next_question"] = next_q_text
                result["status"] = "next_question"
            except Exception as e:
                logger.error("Failed to generate next question: %s", e)
                # If we ran out of questions or LLM failed, end session
                result["status"] = "complete"
                state.is_active = False
                try:
                    session_mgr.save_session(req.session_id, state)
                except Exception:
                    logger.exception("Session save failed for %s", req.session_id)
                result["next_question"] = ""
        else:
            result["status"] = "retry"
            result["follow_up"] = followup
            # Even on retry, pre-load the next question so user can skip forward
            if state.current_question_index < len(state.questions) - 1:
                result["next_question"] = state.questions[state.current_question_index + 1].question
            else:
                result["next_question"] = ""

        return result
    except Exception as e:
        logger.exception("Failed to process answer")
        return error_response(str(e), "answer_failed", "/api/answer")


def _fallback_score(answer_text: str, question_text: str) -> tuple:
    """Return a fallback score when the LLM is down."""
    word_count = len(answer_text.split())
    overall = min(5, max(2, word_count // 10))
    score = AnswerScore(
        overall=overall,
        criteria=ScoringCriteria(),
        strong_points=["Response provided"],
        weak_points=["Could not get LLM scoring — check vLLM status"],
        improved_answer="Try again when the LLM is online.",
        repeat_prompt=f"Redo: {question_text}",
    )
    return score, "Try answering again with more detail."


@app.post("/api/repeat")
async def repeat_drill(req: RepeatDrillRequest):
    """Repeat the same question with a new angle."""
    state = active_sessions.get(req.session_id)
    if not state:
        return JSONResponse(status_code=404, content={"ok": False, "error": "Session not found"})

    try:
        current_q = state.questions[req.question_index]
        try:
            new_question = await interviewer.generate_opening_question(
                state.job_description, state.mode, "challenge, aggressive"
            )
        except Exception as e:
            logger.error("LLM repeat failed: %s", e)
            new_question = InterviewQuestion(
                question=f"Same topic — explain your approach differently: {current_q.question}",
                mode=state.mode,
            )
        state.questions[req.question_index] = new_question
        return {
            "question": new_question.question,
            "status": "new_question",
        }
    except Exception as e:
        logger.exception("Failed to repeat drill")
        return error_response(str(e), "repeat_failed", "/api/repeat")


class NextQuestionRequest(BaseModel):
    session_id: str


@app.post("/api/next")
async def next_question(req: NextQuestionRequest):
    """Advance to the next question in the session."""
    state = active_sessions.get(req.session_id)
    if not state:
        return JSONResponse(status_code=404, content={"ok": False, "error": "Session not found"})

    state.current_question_index += 1
    if state.current_question_index < len(state.questions):
        next_q = state.questions[state.current_question_index]
        return {
            "question": next_q.question,
            "status": "next_question",
            "question_index": state.current_question_index + 1,
        }

    state.is_active = False
    try:
        session_mgr.save_session(req.session_id, state)
    except Exception:
        logger.exception("Session save failed for %s", req.session_id)
    return {"status": "complete"}


# ── Session management ────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/sessions")
async def list_sessions():
    return {"sessions": session_mgr.list_sessions()}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    if session_id in active_sessions:
        del active_sessions[session_id]
    return {"status": "deleted"}


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    state = active_sessions.get(session_id)
    if not state:
        return JSONResponse(status_code=404, content={"ok": False, "error": "Session not found"})
    return {
        "session_id": state.session_id,
        "current_question_index": state.current_question_index,
        "total_questions": len(state.questions),
        "total_answers": len(state.answers),
        "is_active": state.is_active,
    }


# ── WebSocket live channel ─────────────────────────────────────────────

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    state = active_sessions.get(session_id)
    if not state:
        await websocket.close(1008, "Session not found")
        return
    try:
        await websocket.send_json({
            "type": "session_start",
            "question": state.questions[state.current_question_index].question,
            "mode": state.mode.value,
        })
        while state.is_active:
            data = await websocket.receive_json()
            if data.get("type") == "answer":
                answer_text = data.get("answer_text", "")
                current_q = state.questions[state.current_question_index]
                try:
                    score, followup = await interviewer.process_answer_and_followup(
                        current_q.question, answer_text, state.job_description
                    )
                except Exception:
                    score, followup = _fallback_score(answer_text, current_q.question)
                answer = InterviewAnswer(
                    transcript=answer_text,
                    score=score,
                    follow_up=followup if score.overall < 6 else None,
                )
                state.answers.append(answer)
                if score.overall >= 6:
                    state.current_question_index += 1
                    if state.current_question_index < len(state.questions):
                        next_q = state.questions[state.current_question_index]
                        await websocket.send_json({
                            "type": "next_question",
                            "question": next_q.question,
                        })
                    else:
                        state.is_active = False
                        try:
                            session_mgr.save_session(session_id, state)
                        except Exception:
                            logger.exception("WS session save failed")
                        await websocket.send_json({"type": "session_complete"})
                        await websocket.close(1000, "Session complete")
                        break
                else:
                    await websocket.send_json({
                        "type": "retry",
                        "score": score.model_dump(),
                        "follow_up": followup,
                    })
    except WebSocketDisconnect:
        pass
