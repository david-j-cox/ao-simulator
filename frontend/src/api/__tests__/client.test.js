import { describe, it, expect, vi, beforeEach } from 'vitest'
import { runSimulation, downloadCSV, downloadJSON } from '../client'

describe('API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('runSimulation', () => {
    it('returns parsed JSON on success', async () => {
      const mockData = { summary: { total_steps: 100 }, steps: [] }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })

      const result = await runSimulation({ environment: 'two_choice' })
      expect(result).toEqual(mockData)
      expect(fetch).toHaveBeenCalledWith('/api/simulate', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }))
    })

    it('throws on error response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: 'Bad request' }),
      })

      await expect(runSimulation({})).rejects.toThrow('Bad request')
    })
  })

  describe('downloadCSV', () => {
    it('triggers file download', async () => {
      const mockBlob = new Blob(['step,action\n1,choice_a'], { type: 'text/csv' })
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      const mockClick = vi.fn()
      const mockCreateElement = vi.spyOn(document, 'createElement').mockReturnValue({
        href: '',
        download: '',
        click: mockClick,
      })
      const mockCreateObjectURL = vi.fn().mockReturnValue('blob:test')
      const mockRevokeObjectURL = vi.fn()
      global.URL.createObjectURL = mockCreateObjectURL
      global.URL.revokeObjectURL = mockRevokeObjectURL

      await downloadCSV({ environment: 'two_choice' })

      expect(mockClick).toHaveBeenCalled()
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob)
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:test')

      mockCreateElement.mockRestore()
    })
  })

  describe('downloadJSON', () => {
    it('triggers file download', async () => {
      const mockBlob = new Blob(['{}'], { type: 'application/json' })
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: () => Promise.resolve(mockBlob),
      })

      const mockClick = vi.fn()
      const mockCreateElement = vi.spyOn(document, 'createElement').mockReturnValue({
        href: '',
        download: '',
        click: mockClick,
      })
      global.URL.createObjectURL = vi.fn().mockReturnValue('blob:test')
      global.URL.revokeObjectURL = vi.fn()

      await downloadJSON({ environment: 'two_choice' })

      expect(mockClick).toHaveBeenCalled()

      mockCreateElement.mockRestore()
    })
  })
})
