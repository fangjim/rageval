from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path
import re
import numpy as np
import pandas as pd
from datetime import datetime  # Add this at the top of app.py
import random

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates')

@app.template_filter('tojson')
def tojson_filter(s):
    return json.dumps(s, indent=2)

def parse_verbose_logs(logs_str):
    """Parse the verbose logs string into structured data."""
    if not logs_str:
        return {'statements': [], 'claims': [], 'verdicts': []}
    
    print(f"Raw logs: {logs_str}")
    data = {}
    
    # Initialize empty lists
    data['statements'] = []
    data['claims'] = []
    data['verdicts'] = []

    try:
        # Extract statements with more precise pattern matching
        if "Statements:" in logs_str:
            statements_section = logs_str.split("Statements:")[1].split("]")[0] + "]"
            statements_section = statements_section.replace("\n", "").strip()
            print(f"Statements section: {statements_section}")  # Debug print
            
            # Extract strings between quotes
            statements_matches = re.findall(r'"([^"]+)"', statements_section)
            if statements_matches:
                data['statements'] = [s.strip() for s in statements_matches if s.strip()]
                print(f"Found statements: {data['statements']}")

        # Extract claims
        if "Claims:" in logs_str:
            claims_section = logs_str.split("Claims:")[1].split("Verdicts:")[0]
            claims_section = claims_section.replace("\n", "").strip()
            claims_matches = re.findall(r'"([^"]+)"', claims_section)
            if claims_matches:
                data['claims'] = [c.strip() for c in claims_matches if c.strip()]
                print(f"Found claims: {data['claims']}")

        # Extract verdicts with more precise pattern
        if "Verdicts:" in logs_str:
            verdicts_section = logs_str.split("Verdicts:")[1].strip()
            verdict_pattern = r'{\s*"verdict":\s*"([^"]+)"(?:\s*,\s*"reason":\s*"?([^"}]+)"?)?\s*}'
            verdict_matches = re.finditer(verdict_pattern, verdicts_section)
            
            for match in verdict_matches:
                verdict = match.group(1).strip()
                reason = match.group(2).strip('"') if match.group(2) else None
                
                if reason and reason.lower() == 'null':
                    reason = None
                
                data['verdicts'].append({
                    'verdict': verdict,
                    'reason': reason
                })
            print(f"Found verdicts: {data['verdicts']}")

    except Exception as e:
        print(f"Error parsing logs: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("Final parsed data:", data)
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
    test_cases = load_test_cases()
    
    # Define all possible intervals
    score_intervals = [(i/5, (i+1)/5) for i in range(5)]  # 0.0-0.2, 0.2-0.4, etc.
    
    # Define all metrics
    metrics = ["Faithfulness", "Answer Relevancy", "Contextual Precision", "Contextual Recall"]
    
    # Initialize samples_by_metric with all intervals
    samples_by_metric = {metric: {} for metric in metrics}
    for metric in metrics:
        for lower, upper in score_intervals:
            interval_label = f"{lower:.1f} - {upper:.1f}"
            samples_by_metric[metric][interval_label] = []

    # Process test cases
    for test_case in test_cases:
        for metric_data in test_case['metricsData']:
            metric_name = metric_data['name']
            if metric_name not in metrics:
                continue
                
            score = metric_data['score']
            
            # Find appropriate interval
            for lower, upper in score_intervals:
                if lower <= score < upper:
                    interval_label = f"{lower:.1f} - {upper:.1f}"
                    case_data = {
                        'input': test_case['input'],
                        'actualOutput': test_case.get('actualOutput', 'N/A'),
                        'expectedOutput': test_case.get('expectedOutput', 'N/A'),
                        'retrievalContext': test_case.get('retrievalContext', []),
                        'metric': metric_data
                    }
                    samples_by_metric[metric_name][interval_label].append(case_data)
                    break

    # Sample down to 1 per interval
    for metric in samples_by_metric:
        for interval in samples_by_metric[metric]:
            if len(samples_by_metric[metric][interval]) > 1:
                samples_by_metric[metric][interval] = random.sample(
                    samples_by_metric[metric][interval], 1
                )

    return render_template("index.html", samples_by_metric=samples_by_metric)

@app.route("/get_feedback_stats")
def get_feedback_stats():
    feedback_path = Path("feedback.json")
    default_stats = {
        'overall': {'agrees': 0, 'disagrees': 0},
        'by_metric': {},
        'by_interval': {}
    }
    
    if not feedback_path.exists():
        return jsonify(default_stats)
        
    try:
        with open(feedback_path, 'r') as f:
            feedback = json.load(f)
            return jsonify(feedback.get('statistics', default_stats))
    except Exception as e:
        print(f"Error reading feedback file: {e}")
        return jsonify(default_stats)

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    metric_name = data["metricName"]
    interval = data["interval"]
    case_index = data["caseIndex"]
    item_id = data["itemId"]
    agreement = data["agreement"]
    
    feedback_path = Path("feedback.json")
    feedback = {
        'verdicts': [],
        'statistics': {
            'overall': {'agrees': 0, 'disagrees': 0},
            'by_metric': {},
            'by_interval': {}
        }
    }
    
    if feedback_path.exists():
        try:
            with open(feedback_path, 'r') as f:
                feedback = json.load(f)
        except Exception as e:
            print(f"Error reading feedback file: {e}")

    stats = feedback['statistics']
    
    # Ensure structures exist
    if 'overall' not in stats:
        stats['overall'] = {'agrees': 0, 'disagrees': 0}
    if 'by_metric' not in stats:
        stats['by_metric'] = {}
    if 'by_interval' not in stats:
        stats['by_interval'] = {}
    
    # Initialize metric stats if needed
    if metric_name not in stats['by_metric']:
        stats['by_metric'][metric_name] = {'agrees': 0, 'disagrees': 0}
        
    # Initialize interval stats if needed
    if interval not in stats['by_interval']:
        stats['by_interval'][interval] = {'agrees': 0, 'disagrees': 0}

    # Add new verdict
    verdict = {
        'metric': metric_name,
        'interval': interval,
        'case_index': case_index,
        'item_id': item_id,
        'agreement': agreement,
        'timestamp': datetime.now().isoformat()
    }
    
    if 'verdicts' not in feedback:
        feedback['verdicts'] = []
    feedback['verdicts'].append(verdict)
    
    # Update statistics
    if agreement:
        stats['overall']['agrees'] += 1
        stats['by_metric'][metric_name]['agrees'] += 1
        stats['by_interval'][interval]['agrees'] += 1
    else:
        stats['overall']['disagrees'] += 1
        stats['by_metric'][metric_name]['disagrees'] += 1
        stats['by_interval'][interval]['disagrees'] += 1
    
    try:
        with open(feedback_path, 'w') as f:
            json.dump(feedback, f, indent=2)
    except Exception as e:
        print(f"Error writing feedback file: {e}")
        return jsonify({"status": "error", "message": str(e)})
    
    return jsonify({
        "status": "success",
        "statistics": stats
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)