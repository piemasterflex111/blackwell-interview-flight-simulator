"""Models for the Blackwell Interview Flight Simulator."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InterviewMode(str, Enum):
    RECRUITER_SCREEN = "recruiter_screen"
    HIRING_MANAGER = "hiring_manager"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    BEHAVIORAL_STAR = "behavioral_star"
    SYSTEM_DESIGN = "system_design"
    RAPID_FIRE = "rapid_fire"
    PRESSURE_FOLLOWUP = "pressure_followup"


class ScoringCriteria(BaseModel):
    relevance: int = 5
    evidence: int = 5
    structure: int = 5
    technical_depth: int = 5
    clarity: int = 5
    concision: int = 5
    confidence: int = 5


class AnswerScore(BaseModel):
    overall: int = 5
    criteria: ScoringCriteria = ScoringCriteria()
    strong_points: list[str] = Field(default_factory=list)
    weak_points: list[str] = Field(default_factory=list)
    improved_answer: str = ""
    repeat_prompt: str = ""


class InterviewQuestion(BaseModel):
    question: str
    mode: InterviewMode = InterviewMode.TECHNICAL_DEEP_DIVE
    question_id: Optional[str] = None


class InterviewAnswer(BaseModel):
    transcript: str
    score: Optional[AnswerScore] = None
    follow_up: Optional[str] = None
    question_index: int = 0
    attempt_number: int = 1
    is_retry: bool = False
    question_id: Optional[str] = None
    question_text: Optional[str] = None


class SessionState(BaseModel):
    session_id: str
    job_description: str
    role_title: str
    mode: InterviewMode = InterviewMode.TECHNICAL_DEEP_DIVE
    interviewer_style: str = "direct"
    questions: list[InterviewQuestion] = Field(default_factory=list)
    answers: list[InterviewAnswer] = Field(default_factory=list)
    current_question_index: int = 0
    duration_minutes: int = 15
    is_active: bool = True


class StartSessionRequest(BaseModel):
    job_description: str
    role_title: str = "Python Automation Engineer"
    mode: InterviewMode = InterviewMode.TECHNICAL_DEEP_DIVE
    interviewer_style: str = "direct"
    duration_minutes: int = 15
    story_context: Optional[str] = None


class AnswerRequest(BaseModel):
    session_id: str
    answer_text: str


class RepeatDrillRequest(BaseModel):
    session_id: str
    question_index: int
