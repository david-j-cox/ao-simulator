export default function AlgorithmSelector({ value, onChange }) {
  return (
    <div className="config-section">
      <label>Algorithm</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="q_learning">Q-Learning</option>
        <option value="etbd">ETBD</option>
        <option value="mpr">MPR</option>
      </select>
    </div>
  );
}
