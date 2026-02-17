import { useState } from 'react';
import './App.css';
import ConfigPage from './pages/ConfigPage';
import ResultsPage from './pages/ResultsPage';

export default function App() {
  const [results, setResults] = useState(null);

  if (results) {
    return <ResultsPage data={results} onBack={() => setResults(null)} />;
  }

  return <ConfigPage onResults={setResults} />;
}
