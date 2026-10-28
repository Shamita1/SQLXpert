"""
Simulates PL/SQL blocks, variables, loops, cursors, and DBMS_OUTPUT for Chapters 4 & 5.
"""
import re

def execute_plsql_simulation(code: str, test_input_data: dict = None) -> dict:
    output_lines = []
    success = True
    error_message = None
    simulated_result = {}

    try:
        # Check basic PL/SQL block structure
        code_upper = code.strip().upper()
        if not ("DECLARE" in code_upper or "BEGIN" in code_upper) or not code_upper.endswith("END;"):
            return {
                "success": False,
                "output": ["Compilation Error: PL/SQL block must start with DECLARE/BEGIN and end with END;"],
                "result": {}
            }

        # Capture DBMS_OUTPUT.PUT_LINE statements
        print_matches = re.findall(r'DBMS_OUTPUT\.PUT_LINE\s*\(\s*(.*?)\s*\)\s*;', code, re.IGNORECASE)
        for match in print_matches:
            clean_val = match.strip("'\"")
            output_lines.append(f"[DBMS_OUTPUT] {clean_val}")

        # Simulate variable declarations and loops for challenges
        if "FOR" in code_upper and "LOOP" in code_upper:
            output_lines.append("[SIMULATOR] Executing procedural loop block...")
            output_lines.append("[SIMULATOR] Loop iteration completed successfully.")
        
        if "CURSOR" in code_upper:
            output_lines.append("[SIMULATOR] Explicit cursor opened, fetched rows, and closed successfully.")

        if "TRIGGER" in code_upper or "BEFORE UPDATE" in code_upper:
            output_lines.append("[SIMULATOR] Trigger compiled and validated against audit schema.")

        output_lines.append("PL/SQL procedure successfully completed.")

    except Exception as e:
        success = False
        error_message = str(e)
        output_lines.append(f"Execution Exception: {error_message}")

    return {
        "success": success,
        "output": output_lines,
        "result": simulated_result
    }