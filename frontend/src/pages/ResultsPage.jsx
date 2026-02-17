import { downloadCSV, downloadJSON } from '../api/client';
import GridVisualization from '../components/GridVisualization';

export default function ResultsPage({ data, onBack }) {
  const { result, request } = data;
  const { summary } = result;

  const handleCSV = () => downloadCSV(request);
  const handleJSON = () => downloadJSON(request);

  return (
    <div className="results-page">
      <button className="back-btn" onClick={onBack}>Back to Config</button>

      <h1>Simulation Results</h1>

      <div className="summary">
        <h2>Summary</h2>
        <table>
          <tbody>
            <tr><td>Agent</td><td>{summary.agent}</td></tr>
            <tr><td>Environment</td><td>{summary.environment}</td></tr>
            <tr><td>Total Steps</td><td>{summary.total_steps}</td></tr>
            <tr><td>Total Reinforcements</td><td>{summary.total_reinforcements}</td></tr>
            <tr><td>Reinforcement Rate</td><td>{(summary.reinforcement_rate * 100).toFixed(2)}%</td></tr>
          </tbody>
        </table>

        <h3>Action Counts</h3>
        <table>
          <thead>
            <tr><th>Action</th><th>Count</th><th>Proportion</th></tr>
          </thead>
          <tbody>
            {Object.entries(summary.action_counts).map(([action, count]) => (
              <tr key={action}>
                <td>{action}</td>
                <td>{count}</td>
                <td>{((count / summary.total_steps) * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {summary.visit_counts && (
        <GridVisualization
          visitCounts={summary.visit_counts}
          rows={request.grid_config?.rows || 5}
          cols={request.grid_config?.cols || 5}
        />
      )}

      <div className="download-section">
        <h3>Download Data</h3>
        <button onClick={handleCSV}>Download CSV</button>
        <button onClick={handleJSON}>Download JSON</button>
      </div>
    </div>
  );
}
