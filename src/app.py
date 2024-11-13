from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path
import re

app = Flask(__name__)

@app.template_filter('tojson')
def tojson_filter(s):
    return json.dumps(s, indent=2)


def parse_verbose_logs(logs_str):
    """Parse the verbose logs string into structured data."""
    data = {}
    
    # Extract statements
    statements_match = re.search(r'Statements:\s*\[(.*?)\]', logs_str, re.DOTALL)
    if statements_match:
        statements = re.findall(r'"([^"]*)"', statements_match.group(1))
        data['statements'] = [s.strip() for s in statements if s.strip()]

    # Extract truths
    truths_match = re.search(r'Truths.*?:\s*\[(.*?)\]', logs_str, re.DOTALL)
    if truths_match:
        truths = re.findall(r'"([^"]*)"', truths_match.group(1))
        data['truths'] = [t.strip() for t in truths if t.strip()]

    # Extract claims
    claims_match = re.search(r'Claims:\s*\[(.*?)\]', logs_str, re.DOTALL)
    if claims_match:
        claims = re.findall(r'"([^"]*)"', claims_match.group(1))
        data['claims'] = [c.strip() for c in claims if c.strip()]

    # Extract verdicts with modified regex pattern
    verdicts_match = re.search(r'Verdicts:\s*\[(.*?)\](?:\s*$|\s*\n)', logs_str, re.DOTALL)
    if verdicts_match:
        verdicts_str = verdicts_match.group(1)
        verdicts = []
        
        # Modified verdict pattern to better match the JSON-like structure
        verdict_pattern = r'{\s*"verdict":\s*"([^"]+)"(?:\s*,\s*"reason":\s*([^}]+))?\s*}'
        
        for match in re.finditer(verdict_pattern, verdicts_str):
            verdict = match.group(1)
            reason = match.group(2)
            
            # Clean up reason if it exists
            if reason:
                reason = reason.strip('"')
                if reason.lower() == 'null':
                    reason = None
            
            verdicts.append({
                'verdict': verdict.strip(),
                'reason': reason
            })
            
        data['verdicts'] = verdicts

    print("Parsed data:", data)  # Debug print
    return data

app.jinja_env.filters['parse_verbose_logs'] = parse_verbose_logs

def load_test_cases():
    test_cases_path = Path("/home/jim/LLM/rageval/test_cases.json")
    if test_cases_path.exists():
        with open(test_cases_path, "r") as f:
            data = json.load(f)
            return data["testCases"]
    return []

def save_feedback(case_index, metric_name, item_id, agreement):
    feedback_path = Path("feedback.json")
    feedback = {}
    if feedback_path.exists():
        with open(feedback_path, "r") as f:
            feedback = json.load(f)
    
    key = f"case_{case_index}_{metric_name}_{item_id}"
    feedback[key] = agreement
    
    with open(feedback_path, "w") as f:
        json.dump(feedback, f, indent=2)

@app.route("/")
def index():
    print("hello1")
    test_cases = load_test_cases()
    for case in test_cases:
        for metric in case['metricsData']:
            if metric['name'] == "Answer Relevancy":
                log_data = parse_verbose_logs(metric['verboseLogs'])
                print("hello")
                print("Answer Relevancy Verdicts:", log_data.get('verdicts'))
    return render_template("index.html", test_cases=test_cases)

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    case_index = data["caseIndex"]
    metric_name = data["metricName"]
    item_id = data.get("itemId", "overall")
    agreement = data["agreement"]
    
    save_feedback(case_index, metric_name, item_id, agreement)
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)