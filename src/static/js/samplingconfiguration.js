const SamplingConfiguration = () => {
  const [samplesPerInterval, setSamplesPerInterval] = React.useState(1);
  
  const intervals = [
    "0.0 - 0.2",
    "0.2 - 0.4",
    "0.4 - 0.6",
    "0.6 - 0.8",
    "0.8 - 1.0",
    "1.0"
  ];

  const metrics = [
    "Faithfulness",
    "Answer Relevancy", 
    "Contextual Precision",
    "Contextual Recall"
  ];

  const handleSubmit = () => {
    fetch('/get_samples', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        samplesPerInterval: samplesPerInterval
      })
    })
    .then(response => response.text())
    .then(html => {
      document.body.innerHTML = html;
    })
    .catch(error => console.error('Error:', error));
  };

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-4">Test Case Sampling Configuration</h2>
        </div>
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium mb-2">
              Samples per Score Interval
            </label>
            <input 
              type="number" 
              min="1"
              max="10"
              value={samplesPerInterval}
              onChange={(e) => setSamplesPerInterval(parseInt(e.target.value))}
              className="border rounded px-3 py-2 w-24"
            />
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Score Intervals</h3>
            <div className="grid grid-cols-2 gap-4">
              {intervals.map((interval) => (
                <div key={interval} className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-blue-100 border border-blue-300 rounded"></div>
                  <span className="text-sm">{interval}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium mb-2">Metrics</h3>
            <div className="grid grid-cols-2 gap-4">
              {metrics.map((metric) => (
                <div key={metric} className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
                  <span className="text-sm">{metric}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4">
            <button
              onClick={handleSubmit}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            >
              Generate Samples
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};