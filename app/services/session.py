import json
import os
from datetime import datetime
from app.models import InterviewQuestion, InterviewAnswer, SessionState
from pathlib import Path

class SessionManager:
    """Manage interview sessions — create, save, load, and track progress."""

    def __init__(self, sessions_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def create_session_id(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d_%H%M%S")

    def save_session(self, session_id: str, state: SessionState) -> dict:
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save transcript
        transcript: list[dict] = []
        for i, q in enumerate(state.questions):
            entry: dict = {"question": q.question, "mode": q.mode.value}
            if i < len(state.answers):
                ans = state.answers[i]
                entry["answer"] = ans.transcript
                if ans.score:
                    entry["score"] = ans.score.model_dump()
                if ans.follow_up:
                    entry["follow_up"] = ans.follow_up
            transcript.append(entry)

        transcript_path = session_dir / "transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f, indent=2)

        # Save transcript markdown
        md_lines = ["# Interview Session Transcript\n"]
        for entry in transcript:
            md_lines.append(f"## Q: {entry['question']}\n")
            if "answer" in entry:
                md_lines.append(f"**A**: {entry['answer']}\n")
            if "score" in entry:
                score = entry["score"]
                md_lines.append(f"**Score**: {score['overall']}/10\n")
                md_lines.append(f"**Strong**: {', '.join(score.get('strong_points', []))}\n")
                md_lines.append(f"**Weak**: {', '.join(score.get('weak_points', []))}\n")
            md_lines.append("")

        md_path = session_dir / "transcript.md"
        with open(md_path, "w") as f:
            f.write("\n".join(md_lines))

        # Save scores
        scores: list[dict] = []
        for ans in state.answers:
            if ans.score:
                scores.append(ans.score.model_dump())

        scores_path = session_dir / "scores.json"
        with open(scores_path, "w") as f:
            json.dump(scores, f, indent=2)

        # Save weak answers and improved versions
        weak_lines = ["# Weak Answers — Practice These\n"]
        improved_lines = ["# Improved Answers\n"]
        for ans in state.answers:
            if ans.score and ans.score.overall < 7:
                weak_lines.append(f"## Question: {state.questions[state.answers.index(ans)].question}\n")
                weak_lines.append(f"**Your answer**: {ans.transcript}\n")
                weak_lines.append(f"**Score**: {ans.score.overall}/10\n")
                weak_lines.append(f"**Weak points**: {', '.join(ans.score.weak_points)}\n")
                weak_lines.append("")
                improved_lines.append(f"**Better answer**: {ans.score.improved_answer}\n")
                improved_lines.append(f"**Practice prompt**: {ans.score.repeat_prompt}\n")
                improved_lines.append("")

        weak_path = session_dir / "weak_answers.md"
        with open(weak_path, "w") as f:
            f.write("\n".join(weak_lines))

        improved_path = session_dir / "improved_answers.md"
        with open(improved_path, "w") as f:
            f.write("\n".join(improved_lines))

        # Session summary
        avg_score = sum(a.score.overall for a in state.answers if a.score) / max(len([a for a in state.answers if a.score]), 1)
        summary = {
            "session_id": session_id,
            "role": state.role_title,
            "mode": state.mode.value,
            "duration_minutes": state.duration_minutes,
            "total_questions": len(state.questions),
            "total_answers": len(state.answers),
            "average_score": round(avg_score, 1),
            "low_score_count": sum(1 for a in state.answers if a.score and a.score.overall < 7),
            "created_at": datetime.now().isoformat()
        }
        summary_path = session_dir / "session_summary.md"
        with open(summary_path, "w") as f:
            f.write(f"# Session Summary\n\n")
            f.write(f"- **Role**: {summary['role']}\n")
            f.write(f"- **Mode**: {summary['mode']}\n")
            f.write(f"- **Questions**: {summary['total_questions']}\n")
            f.write(f"- **Average Score**: {summary['average_score']}/10\n")
            f.write(f"- **Answers to practice**: {summary['low_score_count']}\n")

        return summary

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
                        "summary": summary_file.read_text()[:200]
                    })
        return sessions
