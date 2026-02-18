import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import GridVisualization from '../GridVisualization'

describe('GridVisualization', () => {
  it('renders heatmap cells', () => {
    const visitCounts = { '(0, 0)': 5, '(0, 1)': 3, '(1, 0)': 1 }
    render(<GridVisualization visitCounts={visitCounts} rows={2} cols={2} />)
    // Should render 4 cells (2x2 grid)
    expect(screen.getByTitle('(0,0): 5 visits')).toBeInTheDocument()
    expect(screen.getByTitle('(0,1): 3 visits')).toBeInTheDocument()
    expect(screen.getByTitle('(1,0): 1 visits')).toBeInTheDocument()
    expect(screen.getByTitle('(1,1): 0 visits')).toBeInTheDocument()
  })

  it('parses string keys correctly', () => {
    const visitCounts = { '(1, 2)': 10 }
    render(<GridVisualization visitCounts={visitCounts} rows={3} cols={3} />)
    expect(screen.getByTitle('(1,2): 10 visits')).toBeInTheDocument()
  })

  it('handles null visitCounts', () => {
    const { container } = render(
      <GridVisualization visitCounts={null} rows={3} cols={3} />
    )
    expect(container.innerHTML).toBe('')
  })
})
