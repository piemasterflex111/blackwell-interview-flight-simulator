"""Session manager — save interview sessions to disk.

Rules:
- One question can have multiple answers (retries).
- Never assume answers and questions are 1:1 by index.
- A save failure must not crash the API.
- Always write all 7 artifacts.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from app.models import InterviewAnswer, SessionState

logger = logging.getLogger(__name__)


def get_question_for_answer(state: SessionState, answer_index: int) -> str:
    """Safely resolve the question text for a given answer index.

    Strategy:
    - If the answer has question_id set, find the matching question.
    - If answer_index maps to a question by position, use that.
    - If out of range but questions exist, use the latest question.
    - If no question exists, return a placeholder.
    """
    # Try by question_id if available
    ans = state.answers[answer_index]
    if ans and ans.question_id:
        for q in state.questions:
            if hasattr(q, "question_id") and getattr(q, "question_id", None) == ans.question_id:
                return q.question

    # Try by position
    if answer_index < len(state.questions):
        return state.questions[answer_index].question

    # Fallback to latest question
    if state.questions:
        return state.questions[-1].question

    return "Unknown question"


class SessionManager:
    """Manage interview sessions — create, save, load, and track progress."""

    def __init__(self, sessions_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session_id(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d_%H%M%S")

    def save_session(self, session_id: str, state: SessionState) -> dict:
        """Save all session artifacts to sessions/<session_id>/."""
        try:
            session_dir = self.sessions_dir / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            self._save_transcript_json(session_dir, state)
            self._save_transcript_md(session_dir, state)
            self._save_scores_json(session_dir, state)
            self._save_weak_answers_md(session_dir, state)
            self._save_improved_answers_md(session_dir, state)
            self._save_repeat_drills_md(session_dir, state)
            self._save_session_summary_md(session_dir, state)

            summary = self._build_summary(state)
            logger.info("Session %s saved (%d questions, %d answers)",
                        session_id, len(state.questions), len(state.answers))
            return summary
        except Exception:
            logger.exception("Failed to save session %s", session_id)
            raise

    # ── Artifact builders ────────────────────────────────────────────

    def _build_transcript(self, state: SessionState) -> list[dict]:
        """Build transcript entries. Answers are grouped by question."""
        transcript = []
        for q_idx, q in enumerate(state.questions):
            entry = {
                "question_index": q_idx,
                "question": q.question,
                "mode": q.mode.value,
                "attempts": [],
            }
            for a_idx, ans in enumerate(state.answers):
                if self._answer_belongs_to_question(state, a_idx, q_idx):
                    attempt = {
                        "answer_index": a_idx,
                        "attempt_number": ans.attempt_number,
                        "is_retry": ans.is_retry,
                        "transcript": ans.transcript,
                    }
                    if ans.score:
                        attempt["score"] = ans.score.model_dump()
                    if ans.follow_up:
                        attempt["follow_up"] = ans.follow_up
                    entry["attempts"].append(attempt)
            # Always append the question entry even with no attempts
            transcript.append(entry)
        return transcript

    def _answer_belongs_to_question(self, state: SessionState,
                                    answer_index: int, question_index: int) -> bool:
        """Check if answer at answer_index belongs to question at question_index."""
        if answer_index >= len(state.answers):
            return False
        ans = state.answers[answer_index]
        # If question_id is set, match by that
        if ans.question_id:
            q_id = getattr(state.questions[question_index], "question_id", None)
            if q_id == ans.question_id:
                return True
        # Fallback: use position-based matching
        return answer_index == question_index

    def _save_transcript_json(self, session_dir: Path, state: SessionState):
        transcript = self._build_transcript(state)
        path = session_dir / "transcript.json"
        with open(path, "w") as f:
            json.dump(transcript, f, indent=2)

    def _save_transcript_md(self, session_dir: Path, state: SessionState):
        lines = ["# Interview Session Transcript\n"]
        transcript = self._build_transcript(state)
        for entry in transcript:
            lines.append(f"## Q: {entry['question']}\n")
            for attempt in entry["attempts"]:
                lines.append(f"**A (attempt {attempt['attempt_number']}):** {attempt['transcript']}\n")
                if "score" in attempt:
                    sc = attempt["score"]
                    lines.append(f"**Score**: {sc['overall']}/10\n")
                    strong = ", ".join(sc.get("strong_points", []))
                    weak = ", ".join(sc.get("weak_points", []))
                    if strong:
                        lines.append(f"**Strong**: {strong}\n")
                    if weak:
                        lines.append(f"**Weak**: {weak}\n")
            if not entry["attempts"]:
                lines.append("*No answer provided*\n")
            lines.append("")

        path = session_dir / "transcript.md"
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def _save_scores_json(self, session_dir: Path, state: SessionState):
        scores = []
        for ans in state.answers:
            if ans.score:
                scores.append(ans.score.model_dump())
        path = session_dir / "scores.json"
        with open(path, "w") as f:
            json.dump(scores, f, indent=2)

    def _save_weak_answers_md(self, session_dir: Path, state: SessionState):
        lines = ["# Weak Answers — Practice These\n"]
        for i, ans in enumerate(state.answers):
            if ans.score and ans.score.overall < 7:
                q_text = get_question_for_answer(state, i)
                lines.append(f"## Question: {q_text}\n")
                lines.append(f"**Your answer**: {ans.transcript}\n")
                lines.append(f"**Score**: {ans.score.overall:d}/10\n")
                lines.append(f"**Weak points**: {', '.join(ans.score.weak_points)}\n")
                lines.append("")
        path = session_dir / "weak_answers.md"
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def _save_improved_answers_md(self, session_dir: Path, state: SessionState):
        lines = ["# Improved Answers\n"]
        for i, ans in enumerate(state.answers):
            if ans.score:
                q_text = get_question_for_answer(state, i)
                lines.append(f"## Question: {q_text}\n")
                lines.append(f"**Your answer**: {ans.transcript}\n")
                lines.append(f"**Better answer**: {ans.score.improved_answer}\n")
                lines.append(f"**Practice prompt**: {ans.score.repeat_prompt}\n")
                lines.append("")
        path = session_dir / "improved_answers.md"
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def _save_repeat_drills_md(self, session_dir: Path, state: SessionState):
        lines = ["# Repeat Drills\n"]
        for i, ans in enumerate(state.answers):
            if ans.score and ans.score.overall < 7:
                q_text = get_question_for_answer(state, i)
                overall = ans.score.overall
                lines.append(f"## Drill: {q_text}\n")
                lines.append(f"**Prompt**: {ans.score.repeat_prompt}\n")
                lines.append(f"**Previous answer**: {ans.transcript}\n")
                lines.append(f"**Target score**: {overall + 3}/10\n")
                lines.append("")
        path = session_dir / "repeat_drills.md"
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def _save_session_summary_md(self, session_dir: Path, state: SessionState):
        summary = self._build_summary(state)
        lines = [
            "# Session Summary\n",
            f"- **Role**: {summary['role']}\n",
            f"- **Mode**: {summary['mode']}\n",
            f"- **Duration**: {summary['duration_minutes']} minutes\n",
            f"- **Questions**: {summary['total_questions']}\n",
            f"- **Total answers**: {summary['total_answers']}\n",
            f"- **Average Score**: {summary['average_score']}/10\n",
            f"- **Answers to practice**: {summary['low_score_count']}\n",
        ]
        path = session_dir / "session_summary.md"
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def _build_summary(self, state: SessionState) -> dict:
        scored = [a for a in state.answers if a.score]
        avg_score = 0.0
        if scored:
            avg_score = sum(a.score.overall for a in scored) / len(scored)
        return {
            "session_id": state.session_id,
            "role": state.role_title,
            "mode": state.mode.value,
            "duration_minutes": state.duration_minutes,
            "total_questions": len(state.questions),
            "total_answers": len(state.answers),
            "average_score": round(avg_score, 1),
            "low_score_count": sum(1 for a in scored if a.score.overall < 7),
        }

    def list_sessions(self) -> list[dict]:
        sessions = []
        if not self.sessions_dir.exists():
            return sessions
        for session_dir in sorted(self.sessions_dir.iterdir()):
            if session_dir.is_dir():
                summary_file = session_dir / "session_summary.md"
                if summary_file.exists():
                    sessions.append({
                        "id": session_dir.name,
                        "path": str(session_dir),
                        "summary": summary_file.read_text()[:200],
                    })
        return sessions
