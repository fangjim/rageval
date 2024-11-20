from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

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

    # Extract verdicts
    verdicts_match = re.search(r'Verdicts:\s*\[(.*?)\](?:\s*$|\s*\n)', logs_str, re.DOTALL)
    if verdicts_match:
        verdicts_str = verdicts_match.group(1)
        verdicts = []
        verdict_pattern = r'{\s*"verdict":\s*"([^"]+)"(?:\s*,\s*"reason":\s*([^}]+))?\s*}'
        
        for match in re.finditer(verdict_pattern, verdicts_str):
            verdict = match.group(1)
            reason = match.group(2)
            
            if reason:
                reason = reason.strip('"')
                if reason.lower() == 'null':
                    reason = None
            
            verdicts.append({
                'verdict': verdict.strip(),
                'reason': reason
            })
            
        data['verdicts'] = verdicts

    return data

app.jinja_env.filters['parse_verbose_logs'] = parse_verbose_logs

def load_test_cases():
    test_cases_path = Path(__file__).parent / "test_cases.json"  # Use relative path
    if test_cases_path.exists():
        with open(test_cases_path, "r") as f:
            data = json.load(f)
            return data["testCases"]
    print(f"Warning: test_cases.json not found at {test_cases_path}")  # Add debug print
    return []

def sample_test_cases(test_cases, samples_per_interval):
    # Convert test cases to DataFrame format
    test_case_info = []
    metrics_scores = {
        "Faithfulness": [],
        "Answer Relevancy": [],
        "Contextual Precision": [],
        "Contextual Recall": []
    }
    
    for test_case in test_cases:
        for metric in test_case['metricsData']:
            metric_name = metric['name']
            if metric_name in metrics_scores:
                test_case_info.append({
                    'input': test_case['input'],
                    'actualOutput': test_case.get('actualOutput', 'N/A'),
                    'expectedOutput': test_case.get('expectedOutput', 'N/A'),
                    'retrievalContext': test_case.get('retrievalContext', []),
                    'score': metric['score'],
                    'metric': metric_name,
                    'reason': metric['reason'],
                    'verboseLogs': metric.get('verboseLogs', ''),
                    'metricsData': test_case['metricsData']
                })
    
    test_case_info_df = pd.DataFrame(test_case_info)
    
    # Define score intervals
    score_intervals = np.arange(0, 1.2, 0.2)
    
    sampled_cases = []
    # Sample cases for each metric and interval
    for metric in metrics_scores.keys():
        metric_df = test_case_info_df[test_case_info_df['metric'] == metric]
        
        for i in range(len(score_intervals) - 1):
            lower_bound = score_intervals[i]
            upper_bound = score_intervals[i + 1]
            
            interval_df = metric_df[
                (metric_df['score'] >= lower_bound) &
                (metric_df['score'] < upper_bound)
            ]
            
            if not interval_df.empty:
                samples = interval_df.sample(n=min(samples_per_interval, len(interval_df)), replace=False)
                for _, sample in samples.iterrows():
                    sampled_cases.append({
                        'input': sample['input'],
                        'actualOutput': sample['actualOutput'],
                        'expectedOutput': sample['expectedOutput'],
                        'retrievalContext': sample['retrievalContext'],
                        'metricsData': sample['metricsData']
                    })
    
    # Remove duplicates based on input field
    unique_cases = []
    seen_inputs = set()
    for case in sampled_cases:
        if case['input'] not in seen_inputs:
            seen_inputs.add(case['input'])
            unique_cases.append(case)
    
    return unique_cases

@app.route("/")
def index():
    return render_template("config.html")

@app.route("/get_samples", methods=["POST"])
def get_samples():
    samples_per_interval = request.json.get('samplesPerInterval', 1)
    test_cases = load_test_cases()
    sampled_cases = sample_test_cases(test_cases, samples_per_interval)
    return render_template("index.html", test_cases=sampled_cases)

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    case_index = data["caseIndex"]
    metric_name = data["metricName"]
    item_id = data.get("itemId", "overall")
    agreement = data["agreement"]
    
    feedback_path = Path("feedback.json")
    feedback = {}
    if feedback_path.exists():
        with open(feedback_path, "r") as f:
            feedback = json.load(f)
    
    key = f"case_{case_index}_{metric_name}_{item_id}"
    feedback[key] = agreement
    
    with open(feedback_path, "w") as f:
        json.dump(feedback, f, indent=2)
    
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)