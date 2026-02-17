export default function EnvironmentSelector({ value, onChange }) {
  return (
    <div className="config-section">
      <label>Environment</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="two_choice">Two-Choice Chamber</option>
        <option value="grid_chamber">Grid Chamber</option>
      </select>
    </div>
  );
}
