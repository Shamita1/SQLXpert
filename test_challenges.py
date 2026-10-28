
from modules.challenges.evaluator import evaluate_submission


# Test 1: Correct answer
result = evaluate_submission(
    1,
    "SELECT name, department FROM students ORDER BY student_id"
)
print("TEST 1 - Correct query:", result["correct"])
print("Feedback:", result["feedback"])
print("Score:", result["score"])


# Test 2: Incorrect answer
result = evaluate_submission(
    1,
    "SELECT name FROM students"
)
print("\nTEST 2 - Incorrect query:", result["correct"])
print("Feedback:", result["feedback"])


# Test 3: Unsafe query
result = evaluate_submission(
    1,
    "DELETE FROM students"
)
print("\nTEST 3 - Unsafe query blocked:", not result["success"])
print("Feedback:", result["feedback"])
