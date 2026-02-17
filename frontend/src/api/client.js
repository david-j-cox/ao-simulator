const API_BASE = '/api';

export async function runSimulation(config) {
  const res = await fetch(`${API_BASE}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Simulation failed');
  }
  return res.json();
}

export async function downloadCSV(config) {
  const res = await fetch(`${API_BASE}/simulate/csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('CSV download failed');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'simulation_results.csv';
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadJSON(config) {
  const res = await fetch(`${API_BASE}/simulate/json`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('JSON download failed');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'simulation_results.json';
  a.click();
  URL.revokeObjectURL(url);
}
