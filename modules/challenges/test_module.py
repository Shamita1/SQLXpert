
from modules.challenges import (
    get_challenges,
    get_challenge,
    submit_challenge
)

print("Total challenges:", len(get_challenges()))
print("Easy challenges:", len(get_challenges("Beginner")))
print("Medium challenges:", len(get_challenges("Intermediate")))
print("First challenge:", get_challenge(1))

# Correct: returns both expected columns.
result = submit_challenge(
    1,
    "SELECT name, department FROM students ORDER BY student_id;"
)
print("Correct submission:", result)

# Incorrect: returns only one column.
result = submit_challenge(
    1,
    "SELECT name FROM students;"
)
print("Incorrect submission:", result)

# Unsafe SQL must be rejected.
result = submit_challenge(1, "DELETE FROM students;")
print("Unsafe submission:", result)
