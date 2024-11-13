import json
import numpy as np
import pandas as pd

# Load JSON data
filename = "/home/jim/LLM/rageval/dummy.json"
with open(filename, 'r') as f:
    data = json.load(f)

# Initialize structures to store metric scores and test case information
metrics_scores = {
    "Faithfulness": [],
    "Answer Relevancy": [],
    "Contextual Precision": [],
    "Contextual Recall": []
}

test_case_info = []

# Extract scores, verbose logs, and test case info
for test_case in data['testCases']:
    input_field = test_case['input']
    actual_output = test_case.get('actualOutput', 'N/A')
    expected_output = test_case.get('expectedOutput', 'N/A')
    retrieval_context = test_case.get('retrievalContext', 'N/A')
    
    for metric in test_case['metricsData']:
        metric_name = metric['name']
        if metric_name in metrics_scores:
            score = metric['score']
            metrics_scores[metric_name].append(score)
            
            # Store the complete information for each test case
            test_case_info.append({
                'input': input_field,
                'actualOutput': actual_output,
                'expectedOutput': expected_output,
                'retrievalContext': retrieval_context,
                'score': score,
                'metric': metric_name,
                'reason': metric['reason'],
                'verboseLogs': metric.get('verboseLogs', '')
            })

# Convert scores to DataFrames for easier manipulation
scores_df = pd.DataFrame(metrics_scores)
test_case_info_df = pd.DataFrame(test_case_info)
# print(test_case_info_df.columns)
# # print(test_case_info_df.head())
# # print(scores_df.head())

score_intervals = np.arange(0, 1.3, 0.2)

def count_scores_by_interval(test_case_info_df, score_intervals):
    counts = {metric: [] for metric in metrics_scores.keys()}
    
    for metric in metrics_scores.keys():
        metric_df = test_case_info_df[test_case_info_df['metric'] == metric]
        
        for i in range(len(score_intervals) - 1):
            lower_bound = score_intervals[i]
            upper_bound = score_intervals[i + 1]
            
            # Filter for scores within the current interval
            interval_df = metric_df[
                (metric_df['score'] >= lower_bound) &
                (metric_df['score'] < upper_bound)
            ]
            
            counts[metric].append(len(interval_df))
            
    return counts

# Count the test cases in each score interval
interval_counts = count_scores_by_interval(test_case_info_df, score_intervals)

# Display interval counts
for metric, counts in interval_counts.items():
    for i in range(len(score_intervals) - 1):
        print(f"{counts[i]} test cases found with {metric} scores in the {score_intervals[i]} - {score_intervals[i + 1]} range.")

def sample_scores_by_interval(test_case_info_df, score_intervals, num_samples_per_interval=1):
    sampled_data = []
    
    # Loop through each metric in the DataFrame
    for metric in metrics_scores.keys():
        metric_df = test_case_info_df[test_case_info_df['metric'] == metric]
        
        # Loop through the intervals
        for i in range(len(score_intervals) - 1):
            lower_bound = score_intervals[i]
            upper_bound = score_intervals[i + 1]
            
            # Filter for scores within the current interval
            interval_df = metric_df[
                (metric_df['score'] >= lower_bound) &
                (metric_df['score'] < upper_bound)
            ]
            
            # Sample multiple entries if available
            if not interval_df.empty:
                sampled_entries = interval_df.sample(n=min(num_samples_per_interval, len(interval_df)), replace=False)
                
                for _, sampled_entry in sampled_entries.iterrows():
                    # Get unique metrics for the same test case
                    test_case_metrics = metric_df[metric_df['input'] == sampled_entry['input']]
                    metrics_info = test_case_metrics[['metric', 'score', 'reason']].drop_duplicates().to_dict(orient='records')
                    
                    # Extract verbose logs (statements, claims, and verdicts)
                    verbose_logs = sampled_entry['verboseLogs']
                    
                    sampled_data.append({
                        'sampled_metric': metric,
                        'sampled_score': sampled_entry['score'],
                        'reason': sampled_entry['reason'],
                        'input': sampled_entry['input'],
                        'actualOutput': sampled_entry['actualOutput'],
                        'expectedOutput': sampled_entry['expectedOutput'],
                        'retrievalContext': sampled_entry['retrievalContext'],
                        'interval': f"{lower_bound} - {upper_bound}",
                        'all_metrics': metrics_info,  # Store all unique metrics information
                        'verboseLogs': verbose_logs  # Include verbose logs (statements, claims, verdicts)
                    })
    
    return pd.DataFrame(sampled_data)

# Specify the number of samples you want per interval
num_samples = 2
sampled_scores_df = sample_scores_by_interval(test_case_info_df, score_intervals, num_samples)

# Display the sampled scores
for index, row in sampled_scores_df.iterrows():
    print(f"--- Sampled Test Case for Metric: {row['sampled_metric']}")
    print(f"Interval: {row['interval']}")
    print(f"Score: {row['sampled_score']:.2f}")
    print(f"Reason: {row['reason']}")
    print(f"Input: {row['input']}")
    print(f"Actual Output: {row['actualOutput']}")
    print(f"Expected Output: {row['expectedOutput']}")
    print(f"Retrieval Context: {row['retrievalContext']}")
    
    # Print verbose logs (statements, claims, verdicts)
    print(f"\nVerbose Logs:\n{row['verboseLogs']}")
    
    # Print other metric scores for the same test case
    print("\nOther Metric Scores:")
    for metric in row['all_metrics']:
        print(f"- Metric: {metric['metric']}, Score: {metric['score']:.2f}, Reason: {metric['reason']}")
    
    print("\n" + "-"*50 + "\n")  # Separator for clarity