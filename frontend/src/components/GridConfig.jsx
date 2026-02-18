const SCHEDULE_TYPES = ['FR', 'VR', 'FI', 'VI'];

export default function GridConfig({ config, onChange }) {
  const update = (field, val) => onChange({ ...config, [field]: parseInt(val) || 0 });

  const updateLever = (index, field, val) => {
    const levers = [...config.levers];
    levers[index] = { ...levers[index], [field]: field === 'magnitude' ? parseFloat(val) || 0 : parseInt(val) || 0 };
    onChange({ ...config, levers });
  };

  const updateLeverSchedule = (index, field, val) => {
    const levers = [...config.levers];
    levers[index] = {
      ...levers[index],
      schedule: { ...levers[index].schedule, [field]: field === 'value' ? (parseInt(val) || 1) : val },
    };
    onChange({ ...config, levers });
  };

  const addLever = () => {
    if (config.levers.length >= 8) return;
    onChange({
      ...config,
      levers: [...config.levers, { row: 0, col: 0, schedule: { type: 'FR', value: 5 }, magnitude: 1.0 }],
    });
  };

  const removeLever = (index) => {
    if (config.levers.length <= 1) return;
    onChange({ ...config, levers: config.levers.filter((_, i) => i !== index) });
  };

  return (
    <div className="config-section">
      <h3>Grid Settings</h3>
      <div className="param-grid">
        <label>Rows <input type="number" min="2" max="20" value={config.rows} onChange={(e) => update('rows', e.target.value)} /></label>
        <label>Cols <input type="number" min="2" max="20" value={config.cols} onChange={(e) => update('cols', e.target.value)} /></label>
        <label>Start Row <input type="number" min="0" value={config.start_row} onChange={(e) => update('start_row', e.target.value)} /></label>
        <label>Start Col <input type="number" min="0" value={config.start_col} onChange={(e) => update('start_col', e.target.value)} /></label>
      </div>

      <h4>Levers</h4>
      {config.levers.map((lever, i) => (
        <div key={i} className="lever-row">
          <span className="lever-label">Lever {i + 1}</span>
          <label>Row <input type="number" min="0" value={lever.row} onChange={(e) => updateLever(i, 'row', e.target.value)} /></label>
          <label>Col <input type="number" min="0" value={lever.col} onChange={(e) => updateLever(i, 'col', e.target.value)} /></label>
          <label>Schedule
            <select value={lever.schedule.type} onChange={(e) => updateLeverSchedule(i, 'type', e.target.value)}>
              {SCHEDULE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <label>Value <input type="number" min="1" value={lever.schedule.value} onChange={(e) => updateLeverSchedule(i, 'value', e.target.value)} /></label>
          <label>Magnitude <input type="number" min="0" step="0.1" value={lever.magnitude} onChange={(e) => updateLever(i, 'magnitude', e.target.value)} /></label>
          {config.levers.length > 1 && (
            <button className="condition-remove-btn" onClick={() => removeLever(i)} title="Remove lever">&times;</button>
          )}
        </div>
      ))}
      {config.levers.length < 8 && (
        <button className="condition-add-btn" onClick={addLever}>+ Add Lever</button>
      )}
    </div>
  );
}
