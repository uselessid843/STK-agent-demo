from flask import Flask, request, jsonify, send_from_directory
from agent import create_agent
from database import SUBMITTERS, SUBMISSIONS, get_missing_submitters
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = Flask(__name__, static_folder='static')
agent_executor = create_agent()

# ── Serve frontend ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# ── PM chat endpoint ─────────────────────────────────────────
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    try:
        from langsmith import Client
        import uuid
        run_id = str(uuid.uuid4())
        result = agent_executor.invoke(
            {'messages': [{'role': 'user', 'content': user_input}]},
            config={'run_id': run_id, 'callbacks': None}
        )
        response = result['messages'][-1].content
        return jsonify({'response': response, 'run_id': run_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Field submission endpoint ────────────────────────────────
@app.route('/api/submit', methods=['POST'])
def submit():
    data = request.json
    required = ['submitter', 'role', 'date', 'raw_input']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    new_submission = {
        'id': f"sub_{len(SUBMISSIONS) + 1:03d}",
        'submitter': data['submitter'],
        'role': data['role'],
        'date': data['date'],
        'raw_input': data['raw_input'],
    }
    SUBMISSIONS.append(new_submission)
    return jsonify({
        'success': True,
        'message': f"Report submitted for {data['submitter']} on {data['date']}."
    })

# ── Submission status endpoint ───────────────────────────────
@app.route('/api/status/<date_str>')
def status(date_str):
    missing = get_missing_submitters(date_str)
    submitted = [
        s for s in SUBMITTERS
        if s['name'] not in [m['name'] for m in missing]
    ]
    return jsonify({
        'date': date_str,
        'submitted': submitted,
        'missing': missing,
    })

# ── Feedback endpoint ────────────────────────────────────────
@app.route('/api/feedback', methods=['POST'])
def feedback():
    data = request.json
    rating = data.get('rating')
    run_id = data.get('run_id')
    message = data.get('message', '')
    print(f"[FEEDBACK] {rating} | {message[:60]}")
    if run_id:
        try:
            from langsmith import Client
            ls_client = Client()
            ls_client.create_feedback(
                run_id=run_id,
                key="quality",
                score=1 if rating == 'up' else 0,
                comment=message[:200]
            )
            print(f"[LANGSMITH] Feedback logged for run {run_id}")
        except Exception as e:
            print(f"[LANGSMITH] Feedback error: {e}")
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=8080)