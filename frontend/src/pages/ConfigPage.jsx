import { useState } from 'react';
import EnvironmentSelector from '../components/EnvironmentSelector';
import AlgorithmSelector from '../components/AlgorithmSelector';
import ScheduleConfig from '../components/ScheduleConfig';
import GridConfig from '../components/GridConfig';
import AlgorithmParams from '../components/AlgorithmParams';
import ConditionEditor, { createDefaultCondition } from '../components/ConditionEditor';
import { runSimulation } from '../api/client';

const DEFAULT_Q = { alpha: 0.1, gamma: 0.9, epsilon: 0.1, history_window: 3 };
const DEFAULT_ETBD = { population_size: 100, mutation_rate: 0.1, fitness_decay: 0.95 };
const DEFAULT_MPR = { initial_arousal: 1.0, activation_decay: 0.95, coupling_floor: 0.01, temperature: 1.0 };
const DEFAULT_GRID = { rows: 5, cols: 5, lever_row: 2, lever_col: 2, start_row: 0, start_col: 0 };

export default function ConfigPage({ onResults }) {
  const [environment, setEnvironment] = useState('two_choice');
  const [algorithm, setAlgorithm] = useState('q_learning');
  const [maxSteps, setMaxSteps] = useState(1000);
  const [seed, setSeed] = useState('');
  const [scheduleA, setScheduleA] = useState({ type: 'VI', value: 30 });
  const [scheduleB, setScheduleB] = useState({ type: 'VI', value: 60 });
  const [schedule, setSchedule] = useState({ type: 'FR', value: 5 });
  const [gridConfig, setGridConfig] = useState(DEFAULT_GRID);
  const [qParams, setQParams] = useState(DEFAULT_Q);
  const [etbdParams, setEtbdParams] = useState(DEFAULT_ETBD);
  const [mprParams, setMprParams] = useState(DEFAULT_MPR);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [multiCondition, setMultiCondition] = useState(false);
  const [conditions, setConditions] = useState([]);

  const getAlgorithmParams = () => {
    if (algorithm === 'q_learning') return qParams;
    if (algorithm === 'etbd') return etbdParams;
    return mprParams;
  };

  const setAlgorithmParams = (params) => {
    if (algorithm === 'q_learning') setQParams(params);
    else if (algorithm === 'etbd') setEtbdParams(params);
    else setMprParams(params);
  };

  const handleMultiConditionToggle = (checked) => {
    setMultiCondition(checked);
    if (checked && conditions.length === 0) {
      // Seed initial condition from current schedule/max_steps values
      const initial = { label: 'Condition 1', max_steps: maxSteps };
      if (environment === 'two_choice') {
        initial.schedule_a = { ...scheduleA };
        initial.schedule_b = { ...scheduleB };
      } else {
        initial.schedule = { ...schedule };
      }
      setConditions([initial]);
    }
  };

  const buildRequest = () => {
    const req = {
      environment,
      algorithm,
      max_steps: maxSteps,
    };
    if (seed !== '') req.seed = parseInt(seed);

    if (multiCondition && conditions.length > 0) {
      req.conditions = conditions;
    } else {
      if (environment === 'two_choice') {
        req.schedule_a = scheduleA;
        req.schedule_b = scheduleB;
      } else {
        req.schedule = schedule;
        req.grid_config = gridConfig;
      }
    }

    if (environment === 'grid_chamber') {
      req.grid_config = gridConfig;
    }

    if (algorithm === 'q_learning') req.q_learning_params = qParams;
    else if (algorithm === 'etbd') req.etbd_params = etbdParams;
    else req.mpr_params = mprParams;

    return req;
  };

  const handleRun = async () => {
    setLoading(true);
    setError('');
    try {
      const req = buildRequest();
      const result = await runSimulation(req);
      onResults({ result, request: req });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="config-page">
      <h1>AO Simulator</h1>
      <p className="subtitle">Configure and run artificial organism simulations</p>

      <EnvironmentSelector value={environment} onChange={setEnvironment} />
      <AlgorithmSelector value={algorithm} onChange={setAlgorithm} />

      <div className="config-section">
        <label className="multi-condition-toggle">
          <input
            type="checkbox"
            checked={multiCondition}
            onChange={(e) => handleMultiConditionToggle(e.target.checked)}
          />
          Multi-condition experiment
        </label>
      </div>

      {multiCondition ? (
        <ConditionEditor
          conditions={conditions}
          environment={environment}
          onChange={setConditions}
        />
      ) : (
        <>
          <ScheduleConfig
            environment={environment}
            scheduleA={scheduleA}
            scheduleB={scheduleB}
            schedule={schedule}
            onChangeA={setScheduleA}
            onChangeB={setScheduleB}
            onChange={setSchedule}
          />
        </>
      )}

      {environment === 'grid_chamber' && (
        <GridConfig config={gridConfig} onChange={setGridConfig} />
      )}

      <AlgorithmParams
        algorithm={algorithm}
        params={getAlgorithmParams()}
        onChange={setAlgorithmParams}
      />

      <div className="config-section">
        <h3>Simulation Settings</h3>
        <div className="param-grid">
          {!multiCondition && (
            <label>Max Steps <input type="number" min="1" max="100000" value={maxSteps} onChange={(e) => setMaxSteps(parseInt(e.target.value) || 1000)} /></label>
          )}
          <label>Seed (optional) <input type="number" value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="Random" /></label>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <button className="run-btn" onClick={handleRun} disabled={loading}>
        {loading ? 'Running...' : 'Run Simulation'}
      </button>
    </div>
  );
}
