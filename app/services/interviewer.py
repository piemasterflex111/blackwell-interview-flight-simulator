import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import LLM_BASE_URL, LLM_MODEL
from app.models import InterviewMode, InterviewQuestion, AnswerScore, ScoringCriteria
from openai import AsyncOpenAI

class InterviewerBrain:
    """Local LLM interviewer that asks questions, follows up, and challenges answers."""

    def __init__(self):
        self.client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key="not-needed")
        self.model = LLM_MODEL
        self.context_history = []

    async def generate_opening_question(self, jd: str, mode: InterviewMode, style: str) -> InterviewQuestion:
        """Generate the first interview question based on JD and mode."""
        system_prompt = self._build_system_prompt(mode, style)
        user_prompt = f"""JOB DESCRIPTION:
{jd}

ASK THE FIRST QUESTION. Ask only ONE question. Make it specific to the role requirements. Do not give advice or commentary — just ask the question."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=200
        )
        content = response.choices[0].message.content
        question_text = content.strip() if content else "Walk me through your background and why this role makes sense."
        self.context_history.append({"role": "assistant", "content": question_text})
        return InterviewQuestion(question=question_text, mode=mode)

    async def process_answer_and_followup(self, question: str, answer: str, jd: str) -> tuple[AnswerScore, str]:
        """Score an answer and generate follow-up question."""
        scoring_prompt = f"""
PREVIOUS QUESTION: {question}
CANDIDATE ANSWER: {answer}

JOB DESCRIPTION CONTEXT:
{jd[:500]}

SCORE THIS ANSWER ON THESE CRITERIA (1-10 each):
- relevance: Does it address the question?
- evidence: Does it cite specific examples, metrics, or technical details?
- structure: Is it organized (context → action → result)?
- technical depth: Does it show real understanding?
- clarity: Can a technical person follow the logic?
- concision: Is it focused without rambling?
- confidence: Does the candidate sound sure of their experience?

RETURN ONLY VALID JSON:
{{
  "overall": 7,
  "criteria": {{
    "relevance": 8,
    "evidence": 6,
    "structure": 7,
    "technical_depth": 5,
    "clarity": 8,
    "concision": 4,
    "confidence": 7
  }},
  "strong_points": ["Good use of specific examples", "Clear structure"],
  "weak_points": ["Could explain the technical architecture more", "Slightly too long"],
  "improved_answer": "A tighter version of the answer",
  "repeat_prompt": "Redo that in 60 seconds. Start with the technical architecture."
}}"""

        scoring_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an interview scorer. Return ONLY valid JSON, no markdown, no commentary."},
                {"role": "user", "content": scoring_prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        score_content = scoring_response.choices[0].message.content
        score_data = json.loads(score_content.strip() if score_content else "{}")
        score = AnswerScore(**score_data)

        # Generate follow-up based on weak points
        followup_prompt = f"""
CANDIDATE JUST ANSWERED: {question}
ANSWER: {answer}
WEAK POINTS: {score.weak_points}

ASK ONE FOLLOW-UP QUESTION that challenges the weakest part of the answer.
Keep it under 50 words. Be direct.
"""

        followup_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._build_system_prompt(InterviewMode.TECHNICAL_DEEP_DIVE, "pressure")},
                {"role": "user", "content": followup_prompt}
            ],
            temperature=0.8,
            max_tokens=150
        )
        followup_content = followup_response.choices[0].message.content
        followup = followup_content.strip() if followup_content else "Can you explain the technical architecture in more detail?"
        return score, followup

    async def generate_daily_practice_questions(self, jd: str, count: int, mode: InterviewMode) -> list[InterviewQuestion]:
        """Generate a set of practice questions for daily drills."""
        prompt = f"""
JOB DESCRIPTION:
{jd[:1000]}

GENERATE {count} INTERVIEW QUESTIONS for {mode.value}.
Return ONLY valid JSON array of objects with fields: question, expected_focus.
Questions should get progressively harder.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=1500
        )
        questions_content = response.choices[0].message.content
        questions = json.loads(questions_content.strip() if questions_content else "[]")
        return [InterviewQuestion(question=q["question"], mode=mode, expected_focus=q["expected_focus"]) for q in questions]

    def _build_system_prompt(self, mode: InterviewMode, style: str) -> str:
        base = f"""You are conducting a {mode.value.replace('_', ' ')} interview for a technical role.
Your style is: {style}.
Ask one question at a time. Be direct. Challenge unsupported claims. Ask for specifics."""

        if mode == InterviewMode.RECUITER_SCREEN:
            base += " Focus on background, motivation, and role fit. Keep questions conversational."
        elif mode == InterviewMode.TECHNICAL_DEEP_DIVE:
            base += " Ask about architecture, implementation details, trade-offs, and failure modes."
        elif mode == InterviewMode.BEHAVIORAL_STAR:
            base += " Push for STAR format: Situation, Task, Action, Result. Ask for specific examples."
        elif mode == InterviewMode.PRESSURE_FOLLOWUP:
            base += " Be skeptical. Interrupt rambling. Ask 'what exactly did you build?' and 'was this production?'"

        return base
