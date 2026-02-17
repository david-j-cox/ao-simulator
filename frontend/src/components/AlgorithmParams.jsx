function NumberParam({ label, value, onChange, min, max, step }) {
  return (
    <label>
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={step || 0.01}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
    </label>
  );
}

function QLearningParams({ params, onChange }) {
  const update = (k, v) => onChange({ ...params, [k]: v });
  return (
    <div className="param-grid">
      <NumberParam label="Alpha (learning rate)" value={params.alpha} onChange={(v) => update('alpha', v)} min={0} max={1} />
      <NumberParam label="Gamma (discount)" value={params.gamma} onChange={(v) => update('gamma', v)} min={0} max={1} />
      <NumberParam label="Epsilon (exploration)" value={params.epsilon} onChange={(v) => update('epsilon', v)} min={0} max={1} />
      <NumberParam label="History Window" value={params.history_window} onChange={(v) => update('history_window', Math.max(1, Math.round(v)))} min={1} step={1} />
    </div>
  );
}

function ETBDParams({ params, onChange }) {
  const update = (k, v) => onChange({ ...params, [k]: v });
  return (
    <div className="param-grid">
      <NumberParam label="Population Size" value={params.population_size} onChange={(v) => update('population_size', Math.max(10, Math.round(v)))} min={10} step={10} />
      <NumberParam label="Mutation Rate" value={params.mutation_rate} onChange={(v) => update('mutation_rate', v)} min={0} max={1} />
      <NumberParam label="Fitness Decay" value={params.fitness_decay} onChange={(v) => update('fitness_decay', v)} min={0} max={1} />
    </div>
  );
}

function MPRParams({ params, onChange }) {
  const update = (k, v) => onChange({ ...params, [k]: v });
  return (
    <div className="param-grid">
      <NumberParam label="Initial Arousal (a)" value={params.initial_arousal} onChange={(v) => update('initial_arousal', v)} min={0.01} />
      <NumberParam label="Activation Decay (b)" value={params.activation_decay} onChange={(v) => update('activation_decay', v)} min={0.01} />
      <NumberParam label="Coupling Floor" value={params.coupling_floor} onChange={(v) => update('coupling_floor', v)} min={0} />
      <NumberParam label="Temperature (grid)" value={params.temperature} onChange={(v) => update('temperature', v)} min={0.01} />
    </div>
  );
}

export default function AlgorithmParams({ algorithm, params, onChange }) {
  return (
    <div className="config-section">
      <h3>{algorithm.toUpperCase()} Parameters</h3>
      {algorithm === 'q_learning' && <QLearningParams params={params} onChange={onChange} />}
      {algorithm === 'etbd' && <ETBDParams params={params} onChange={onChange} />}
      {algorithm === 'mpr' && <MPRParams params={params} onChange={onChange} />}
    </div>
  );
}
