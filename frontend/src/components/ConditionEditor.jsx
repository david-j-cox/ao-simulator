const SCHEDULE_TYPES = ['FR', 'VR', 'FI', 'VI'];

function ScheduleInput({ label, schedule, onChange }) {
  return (
    <div className="schedule-input">
      <label>{label}</label>
      <select
        value={schedule.type}
        onChange={(e) => onChange({ ...schedule, type: e.target.value })}
      >
        {SCHEDULE_TYPES.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
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

function ConditionCard({ condition, index, environment, onChange, onRemove, canRemove }) {
  const update = (field, value) => {
    onChange({ ...condition, [field]: value });
  };

  return (
    <div className="condition-card">
      <div className="condition-card-header">
        <span className="condition-number">Condition {index + 1}</span>
        {canRemove && (
          <button className="condition-remove-btn" onClick={onRemove} title="Remove condition">
            &times;
          </button>
        )}
      </div>

      <div className="condition-card-body">
        <label className="condition-label-input">
          Label
          <input
            type="text"
            value={condition.label}
            onChange={(e) => update('label', e.target.value)}
            placeholder={`Condition ${index + 1}`}
          />
        </label>

        <label className="condition-label-input">
          Max Steps
          <input
            type="number"
            min="1"
            max="100000"
            value={condition.max_steps}
            onChange={(e) => update('max_steps', parseInt(e.target.value) || 1000)}
          />
        </label>

        {environment === 'two_choice' ? (
          <>
            <ScheduleInput
              label="Schedule A"
              schedule={condition.schedule_a}
              onChange={(s) => update('schedule_a', s)}
            />
            <ScheduleInput
              label="Schedule B"
              schedule={condition.schedule_b}
              onChange={(s) => update('schedule_b', s)}
            />
          </>
        ) : (
          <ScheduleInput
            label="Schedule"
            schedule={condition.schedule}
            onChange={(s) => update('schedule', s)}
          />
        )}
      </div>
    </div>
  );
}

export function createDefaultCondition(environment, index) {
  const base = {
    label: `Condition ${index + 1}`,
    max_steps: 1000,
  };
  if (environment === 'two_choice') {
    base.schedule_a = { type: 'VI', value: 30 };
    base.schedule_b = { type: 'VI', value: 60 };
  } else {
    base.schedule = { type: 'FR', value: 5 };
  }
  return base;
}

export default function ConditionEditor({ conditions, environment, onChange }) {
  const addCondition = () => {
    if (conditions.length >= 6) return;
    onChange([...conditions, createDefaultCondition(environment, conditions.length)]);
  };

  const removeCondition = (index) => {
    if (conditions.length <= 1) return;
    onChange(conditions.filter((_, i) => i !== index));
  };

  const updateCondition = (index, updated) => {
    const next = [...conditions];
    next[index] = updated;
    onChange(next);
  };

  return (
    <div className="config-section">
      <h3>Conditions</h3>
      <div className="condition-list">
        {conditions.map((cond, i) => (
          <ConditionCard
            key={i}
            condition={cond}
            index={i}
            environment={environment}
            onChange={(updated) => updateCondition(i, updated)}
            onRemove={() => removeCondition(i)}
            canRemove={conditions.length > 1}
          />
        ))}
      </div>
      {conditions.length < 6 && (
        <button className="condition-add-btn" onClick={addCondition}>
          + Add Condition
        </button>
      )}
    </div>
  );
}
