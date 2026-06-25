from pydantic import BaseModel
from typing import Optional
from enum import Enum

class InterviewMode(str, Enum):
    RECUITER_SCREEN = "recruiter_screen"
    HIRING_MANAGER = "hiring_manager"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    BEHAVIORAL_STAR = "behavioral_star"
    SYSTEM_DESIGN = "system_design"
    RAPID_FIRE = "rapid_fire"
    PRESSURE_FOLLOWUP = "pressure_followup"

class ScoringCriteria(BaseModel):
    relevance: int
    evidence: int
    structure: int
    technical_depth: int
    clarity: int
    concision: int
    confidence: int

class AnswerScore(BaseModel):
    overall: int
    criteria: ScoringCriteria
    strong_points: list[str]
    weak_points: list[str]
    improved_answer: str
    repeat_prompt: str

class InterviewQuestion(BaseModel):
    question: str
    mode: InterviewMode
    follow_up: Optional[str] = None
    expected_focus: Optional[str] = None

class InterviewAnswer(BaseModel):
    transcript: str
    score: Optional[AnswerScore] = None
    follow_up: Optional[str] = None

class SessionState(BaseModel):
    job_description: str
    role_title: str
    mode: InterviewMode
    interviewer_style: str
    duration_minutes: int
    questions: list[InterviewQuestion] = []
    answers: list[InterviewAnswer] = []
    current_question_index: int = 0
    is_active: bool = False
