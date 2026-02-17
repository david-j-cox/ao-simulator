function ScheduleInput({ label, schedule, onChange }) {
  return (
    <div className="schedule-input">
      <label>{label}</label>
      <select
        value={schedule.type}
        onChange={(e) => onChange({ ...schedule, type: e.target.value })}
      >
        <option value="FR">FR (Fixed Ratio)</option>
        <option value="VR">VR (Variable Ratio)</option>
        <option value="FI">FI (Fixed Interval)</option>
        <option value="VI">VI (Variable Interval)</option>
      </select>
      <input
        type="number"
        min="1"
        value={schedule.value}
        onChange={(e) => onChange({ ...schedule, value: parseInt(e.target.value) || 1 })}
      />
    </div>
  );
}

export default function ScheduleConfig({ environment, scheduleA, scheduleB, schedule, onChangeA, onChangeB, onChange }) {
  if (environment === 'two_choice') {
    return (
      <div className="config-section">
        <h3>Schedules</h3>
        <ScheduleInput label="Schedule A" schedule={scheduleA} onChange={onChangeA} />
        <ScheduleInput label="Schedule B" schedule={scheduleB} onChange={onChangeB} />
      </div>
    );
  }
  return (
    <div className="config-section">
      <h3>Lever Schedule</h3>
      <ScheduleInput label="Schedule" schedule={schedule} onChange={onChange} />
    </div>
  );
}
