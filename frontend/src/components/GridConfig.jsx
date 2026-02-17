export default function GridConfig({ config, onChange }) {
  const update = (field, val) => onChange({ ...config, [field]: parseInt(val) || 0 });

  return (
    <div className="config-section">
      <h3>Grid Settings</h3>
      <div className="param-grid">
        <label>Rows <input type="number" min="2" max="20" value={config.rows} onChange={(e) => update('rows', e.target.value)} /></label>
        <label>Cols <input type="number" min="2" max="20" value={config.cols} onChange={(e) => update('cols', e.target.value)} /></label>
        <label>Lever Row <input type="number" min="0" value={config.lever_row} onChange={(e) => update('lever_row', e.target.value)} /></label>
        <label>Lever Col <input type="number" min="0" value={config.lever_col} onChange={(e) => update('lever_col', e.target.value)} /></label>
        <label>Start Row <input type="number" min="0" value={config.start_row} onChange={(e) => update('start_row', e.target.value)} /></label>
        <label>Start Col <input type="number" min="0" value={config.start_col} onChange={(e) => update('start_col', e.target.value)} /></label>
      </div>
    </div>
  );
}
