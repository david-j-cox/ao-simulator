import { useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, ResponsiveContainer, Legend,
} from 'recharts';

const COLORS = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777'];

export default function CumulativeRecordChart({ steps, conditionSummaries, environment }) {
  const isTwoChoice = environment === 'two_choice';

  const data = useMemo(() => {
    let cumA = 0;
    let cumB = 0;
    let cumTotal = 0;

    return steps.map((s) => {
      if (isTwoChoice) {
        if (s.action === 'choice_a') cumA++;
        else if (s.action === 'choice_b') cumB++;
        return { step: s.step, cumA, cumB };
      } else {
        if (s.action === 'press_lever') cumTotal++;
        return { step: s.step, cumTotal };
      }
    });
  }, [steps, isTwoChoice]);

  const boundaries = useMemo(() => {
    if (!conditionSummaries || conditionSummaries.length <= 1) return [];
    return conditionSummaries.slice(1).map((cs) => ({
      step: cs.start_step,
      label: cs.label,
    }));
  }, [conditionSummaries]);

  return (
    <div className="chart-container">
      <h3>Cumulative Record</h3>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="step"
            label={{ value: 'Step', position: 'insideBottom', offset: -2 }}
          />
          <YAxis label={{ value: 'Cumulative Responses', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />

          {isTwoChoice ? (
            <>
              <Line
                type="monotone"
                dataKey="cumA"
                name="Choice A"
                stroke={COLORS[0]}
                dot={false}
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="cumB"
                name="Choice B"
                stroke={COLORS[1]}
                dot={false}
                strokeWidth={2}
              />
            </>
          ) : (
            <Line
              type="monotone"
              dataKey="cumTotal"
              name="Lever Presses"
              stroke={COLORS[0]}
              dot={false}
              strokeWidth={2}
            />
          )}

          {boundaries.map((b, i) => (
            <ReferenceLine
              key={i}
              x={b.step}
              stroke="#666"
              strokeDasharray="5 5"
              label={{ value: b.label, position: 'top', fill: '#666', fontSize: 11 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
