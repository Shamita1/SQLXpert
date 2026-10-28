
from .problem_bank import CHALLENGES
from .evaluator import evaluate_submission


def get_challenges(difficulty=None, topic=None):
    """Return public challenge details, optionally filtered."""

    level_aliases = {
        "beginner": {"beginner", "easy"},
        "intermediate": {"intermediate", "medium"},
        "advanced": {"advanced", "hard"},
    }

    questions = []

    for question in CHALLENGES:
        level = question.get("difficulty", "").lower()

        if difficulty:
            requested = difficulty.lower()
            accepted_levels = level_aliases.get(requested, {requested})
            if level not in accepted_levels:
                continue

        if topic and topic.lower() not in question.get("topic", "").lower():
            continue

        # Never expose answers or setup SQL to the frontend.
        public_question = {
            key: value
            for key, value in question.items()
            if key not in {
                "solution_sql", "expected_sql", "setup_sql", "sample_data"
            }
        }
        questions.append(public_question)

    return questions


def get_challenge(challenge_id):
    """Get one challenge without exposing its answer."""

    for question in CHALLENGES:
        if question["id"] == challenge_id:
            return {
                key: value
                for key, value in question.items()
                if key not in {
                    "solution_sql", "expected_sql", "setup_sql", "sample_data"
                }
            }

    return None


def submit_challenge(challenge_id, sql):
    """Evaluate SQL and return feedback and points."""

    question = next(
        (q for q in CHALLENGES if q["id"] == challenge_id),
        None
    )

    if question is None:
        return {
            "success": False,
            "correct": False,
            "feedback": "Challenge not found.",
            "score": 0,
            "hint": ""
        }

    result = evaluate_submission(challenge_id, sql)

    return {
        "success": result.get("success", False),
        "correct": result.get("correct", False),
        "feedback": result.get("feedback", "Evaluation complete."),
        "score": result.get("score", 0),
        "max_score": result.get("max_score", question.get("points", 10)),
        "hint": "" if result.get("correct") else question.get("hint", ""),
        "columns": result.get("columns", []),
        "rows": result.get("rows", [])
    }
