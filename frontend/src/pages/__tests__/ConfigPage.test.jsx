import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfigPage from '../ConfigPage'

// Mock the API client to prevent actual fetch calls
vi.mock('../../api/client', () => ({
  runSimulation: vi.fn(),
}))

describe('ConfigPage', () => {
  const mockOnResults = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form elements', () => {
    render(<ConfigPage onResults={mockOnResults} />)
    expect(screen.getByText('AO Simulator')).toBeInTheDocument()
    expect(screen.getByText('Run Simulation')).toBeInTheDocument()
  })

  it('renders environment and algorithm selectors', () => {
    render(<ConfigPage onResults={mockOnResults} />)
    // Should have select elements for environment and algorithm
    const selects = screen.getAllByRole('combobox')
    expect(selects.length).toBeGreaterThanOrEqual(2)
  })

  it('shows multi-condition checkbox', () => {
    render(<ConfigPage onResults={mockOnResults} />)
    const checkbox = screen.getByLabelText(/multi-condition/i)
    expect(checkbox).toBeInTheDocument()
    expect(checkbox).not.toBeChecked()
  })

  it('toggles multi-condition mode', () => {
    render(<ConfigPage onResults={mockOnResults} />)
    const checkbox = screen.getByLabelText(/multi-condition/i)
    fireEvent.click(checkbox)
    expect(checkbox).toBeChecked()
  })

  it('renders run button', () => {
    render(<ConfigPage onResults={mockOnResults} />)
    const runBtn = screen.getByText('Run Simulation')
    expect(runBtn).toBeInTheDocument()
    expect(runBtn).not.toBeDisabled()
  })
})
