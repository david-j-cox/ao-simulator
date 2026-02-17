export default function GridVisualization({ visitCounts, rows, cols }) {
  if (!visitCounts) return null;

  // Parse visit counts from string keys like "(2, 3)" to grid
  const grid = Array.from({ length: rows }, () => Array(cols).fill(0));
  let maxCount = 1;

  for (const [key, count] of Object.entries(visitCounts)) {
    const match = key.match(/\((\d+),\s*(\d+)\)/);
    if (match) {
      const r = parseInt(match[1]);
      const c = parseInt(match[2]);
      if (r < rows && c < cols) {
        grid[r][c] = count;
        maxCount = Math.max(maxCount, count);
      }
    }
  }

  const cellSize = 48;

  return (
    <div className="grid-viz">
      <h3>Visit Frequency Heatmap</h3>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
          gap: '2px',
        }}
      >
        {grid.map((row, r) =>
          row.map((count, c) => {
            const intensity = count / maxCount;
            const bg = `rgba(59, 130, 246, ${0.1 + intensity * 0.85})`;
            return (
              <div
                key={`${r}-${c}`}
                style={{
                  width: cellSize,
                  height: cellSize,
                  backgroundColor: bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  color: intensity > 0.5 ? '#fff' : '#333',
                  borderRadius: '4px',
                }}
                title={`(${r},${c}): ${count} visits`}
              >
                {count}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
