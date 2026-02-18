import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import CumulativeRecordChart from '../CumulativeRecordChart'

// Mock recharts to avoid SVG rendering issues in jsdom
vi.mock('recharts', () => {
  const MockResponsiveContainer = ({ children }) => <div data-testid="responsive-container">{children}</div>
  const MockLineChart = ({ children, data }) => <div data-testid="line-chart" data-count={data?.length}>{children}</div>
  const MockLine = ({ dataKey, name }) => <div data-testid={`line-${dataKey}`} data-name={name} />
  const MockReferenceLine = ({ label }) => <div data-testid="reference-line" data-label={label?.value} />
  return {
    ResponsiveContainer: MockResponsiveContainer,
    LineChart: MockLineChart,
    Line: MockLine,
    XAxis: () => null,
    YAxis: () => null,
    CartesianGrid: () => null,
    Tooltip: () => null,
    Legend: () => null,
    ReferenceLine: MockReferenceLine,
  }
})

const twoChoiceSteps = [
  { step: 1, action: 'choice_a', reinforced: false },
  { step: 2, action: 'choice_b', reinforced: true },
  { step: 3, action: 'choice_a', reinforced: false },
]

const gridSteps = [
  { step: 1, action: 'up', reinforced: false },
  { step: 2, action: 'press_lever', reinforced: true },
  { step: 3, action: 'down', reinforced: false },
]

describe('CumulativeRecordChart', () => {
  it('renders two lines for two-choice', () => {
    render(
      <CumulativeRecordChart
        steps={twoChoiceSteps}
        conditionSummaries={[]}
        environment="two_choice"
      />
    )
    expect(screen.getByTestId('line-cumA')).toBeInTheDocument()
    expect(screen.getByTestId('line-cumB')).toBeInTheDocument()
  })

  it('renders one line for grid', () => {
    render(
      <CumulativeRecordChart
        steps={gridSteps}
        conditionSummaries={[]}
        environment="grid_chamber"
      />
    )
    expect(screen.getByTestId('line-cumTotal')).toBeInTheDocument()
    expect(screen.queryByTestId('line-cumA')).not.toBeInTheDocument()
  })

  it('renders condition boundaries', () => {
    const summaries = [
      { condition: 1, label: 'Baseline', start_step: 1, end_step: 3 },
      { condition: 2, label: 'Extinction', start_step: 4, end_step: 6 },
    ]
    render(
      <CumulativeRecordChart
        steps={twoChoiceSteps}
        conditionSummaries={summaries}
        environment="two_choice"
      />
    )
    const refLines = screen.getAllByTestId('reference-line')
    expect(refLines).toHaveLength(1) // boundary before 2nd condition
    expect(refLines[0]).toHaveAttribute('data-label', 'Extinction')
  })
})
