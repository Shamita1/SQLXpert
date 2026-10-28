let editor = null;
let timerInterval = null;
let timerSeconds = 300; // Default fallback
let totalChallengeTime = 300;

// Initialize Monaco Editor on page load
require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.39.0/min/vs' }});
require(['vs/editor/editor.main'], function() {
    editor = monaco.editor.create(document.getElementById('monaco-editor-container'), {
        value: '-- Write your SQL or PL/SQL query here\nSELECT * FROM students;',
        language: 'sql',
        theme: 'vs-dark',
        automaticLayout: true,
        fontSize: 14
    });
});

function startCountdown(seconds) {
    timerSeconds = seconds;
    totalChallengeTime = seconds;
    const timerDisplay = document.getElementById('countdown-timer');
    
    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        if (timerSeconds <= 0) {
            clearInterval(timerInterval);
            alert("⏰ Time's up! Challenge failed.");
            window.location.href = "/challenges";
            return;
        }
        timerSeconds--;
        let mins = Math.floor(timerSeconds / 60);
        let secs = timerSeconds % 60;
        timerDisplay.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }, 1000);
}

async function runTests() {
    if (!editor) return;
    const code = editor.getValue();
    const isPlSql = window.isPlSqlChallenge || false;

    const logBox = document.getElementById('console-output-log');
    logBox.textContent = "Executing query against engine...";

    try {
        const response = await fetch('/api/challenges/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, is_plsql: isPlSql })
        });
        const data = await response.json();

        if (data.success) {
            let outputText = data.output ? data.output.join('\n') : "Query executed successfully.\n";
            if (data.rows && data.rows.length > 0) {
                outputText += `\nReturned ${data.rows.length} row(s).\n`;
                outputText += JSON.stringify(data.rows.slice(0, 5), null, 2);
            }
            logBox.textContent = outputText;
            logBox.style.color = "#4ade80"; // Green for success
        } else {
            logBox.textContent = "Execution Error:\n" + (data.output ? data.output.join('\n') : "Unknown error");
            logBox.style.color = "#f87171"; // Red for error
        }
    } catch (err) {
        logBox.textContent = "Network or Server Exception: " + err.message;
        logBox.style.color = "#f87171";
    }
}

async function submitSolution() {
    if (!editor) return;
    clearInterval(timerInterval);

    const challengeId = window.currentChallengeId || "ch1_q1";
    const timeRemaining = timerSeconds;

    try {
        const response = await fetch('/api/challenges/complete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                challenge_id: challengeId,
                time_remaining: timeRemaining,
                total_time: totalChallengeTime,
                base_xp: 100,
                base_coins: 25
            })
        });
        const data = await response.json();

        if (data.success) {
            alert(`🎉 Success! ${data.message}`);
            window.location.href = "/challenges";
        } else {
            alert("Submission failed to process rewards.");
        }
    } catch (err) {
        alert("Error submitting solution: " + err.message);
    }
}

async function buyItem(itemId) {
    try {
        const response = await fetch('/api/shop/buy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        });
        const data = await response.json();

        if (data.success) {
            alert(data.message);
            location.reload(); // Refresh to update coin balance
        } else {
            alert("Purchase failed: " + data.error);
        }
    } catch (err) {
        alert("Transaction error: " + err.message);
    }
}