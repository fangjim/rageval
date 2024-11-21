// Debug flag
const DEBUG = true;

// Global statistics object
let feedbackStats = {
    overall: { agrees: 0, disagrees: 0 },
    by_metric: {},
    by_interval: {}
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing feedback handlers');
    initializeFeedback();
});

function initializeFeedback() {
    console.log('Initializing feedback handlers');
    
    // Load existing stats
    fetch('/get_feedback_stats')
        .then(response => response.json())
        .then(data => {
            console.log('Loaded stats:', data);
            feedbackStats = data;
            updateStatisticsDisplay();
        })
        .catch(err => console.error('Error loading stats:', err));

    // Add click handlers to all feedback buttons
    document.querySelectorAll('.agree, .disagree').forEach(button => {
        console.log('Adding handler to button:', button);
        button.onclick = function() {
            const metricName = this.dataset.metric;
            const interval = this.dataset.interval;
            const caseIndex = this.dataset.caseIndex;
            const itemId = this.dataset.itemId;
            const isAgree = this.classList.contains('agree');

            console.log('Button clicked:', {
                metricName,
                interval,
                caseIndex,
                itemId,
                isAgree
            });

            // Update UI
            const buttonGroup = this.parentElement;
            buttonGroup.querySelectorAll('button').forEach(btn => 
                btn.classList.remove('selected')
            );
            this.classList.add('selected');

            // Submit feedback
            fetch('/submit_feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    metricName,
                    interval,
                    caseIndex,
                    itemId,
                    agreement: isAgree
                })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Feedback submitted:', data);
                if (data.statistics) {
                    feedbackStats = data.statistics;
                    updateStatisticsDisplay();
                }
            })
            .catch(err => console.error('Error submitting feedback:', err));
        };
    });
}

function updateStatisticsDisplay() {
    console.log('Updating statistics display:', feedbackStats);
    
    // Update overall stats
    const totalVerdicts = feedbackStats.overall.agrees + feedbackStats.overall.disagrees;
    const overallRate = calculateAgreementRate(feedbackStats.overall.agrees, feedbackStats.overall.disagrees);
    
    document.getElementById('overall-agreement').textContent = `${overallRate}%`;
    document.getElementById('total-agrees').textContent = feedbackStats.overall.agrees;
    document.getElementById('total-verdicts').textContent = totalVerdicts;

    // Update metric stats
    const metricStatsHtml = Object.entries(feedbackStats.by_metric)
        .map(([metric, stats]) => {
            const rate = calculateAgreementRate(stats.agrees, stats.disagrees);
            return `
                <div class="stat-item">
                    <span class="stat-label">${metric}</span>
                    <span class="stat-value">${rate}%</span>
                    <span class="stat-detail">(${stats.agrees}/${stats.agrees + stats.disagrees})</span>
                </div>
            `;
        })
        .join('');
    document.getElementById('metric-stats').innerHTML = metricStatsHtml;

    // Update interval stats
    const intervalStatsHtml = Object.entries(feedbackStats.by_interval)
        .map(([interval, stats]) => {
            const rate = calculateAgreementRate(stats.agrees, stats.disagrees);
            return `
                <div class="stat-item">
                    <span class="stat-label">${interval}</span>
                    <span class="stat-value">${rate}%</span>
                    <span class="stat-detail">(${stats.agrees}/${stats.agrees + stats.disagrees})</span>
                </div>
            `;
        })
        .join('');
    document.getElementById('interval-stats').innerHTML = intervalStatsHtml;
}

function calculateAgreementRate(agrees, disagrees) {
    const total = agrees + disagrees;
    if (total === 0) return 0;
    return (agrees / total * 100).toFixed(1);
}