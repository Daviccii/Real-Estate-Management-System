import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import Pagination from './Pagination'

describe('Pagination', () => {
  it('renders nothing when there is a single page and nothing more to load', () => {
    const { container } = render(<Pagination page={1} hasMore={false} onPrev={() => {}} onNext={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows "Page N of M" once the total is known', () => {
    render(<Pagination page={2} totalPages={5} hasMore onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByText('Page 2 of 5')).toBeInTheDocument()
  })

  it('falls back to a bare page number when the total is unknown', () => {
    render(<Pagination page={3} hasMore onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByText('Page 3')).toBeInTheDocument()
  })

  it('disables Previous on the first page and Next on the last', () => {
    const { rerender } = render(<Pagination page={1} totalPages={3} hasMore onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next' })).toBeEnabled()

    rerender(<Pagination page={3} totalPages={3} hasMore={false} onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByRole('button', { name: 'Previous' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })

  it('locks both buttons while a page is loading', () => {
    render(<Pagination page={2} totalPages={4} hasMore loading onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })

  it('calls the handlers', async () => {
    const onPrev = vi.fn()
    const onNext = vi.fn()
    render(<Pagination page={2} totalPages={4} hasMore onPrev={onPrev} onNext={onNext} />)

    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.click(screen.getByRole('button', { name: 'Previous' }))

    expect(onNext).toHaveBeenCalledTimes(1)
    expect(onPrev).toHaveBeenCalledTimes(1)
  })

  it('treats an unknown total as "no more pages" when hasMore is false', () => {
    render(<Pagination page={2} hasMore={false} onPrev={() => {}} onNext={() => {}} />)
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })
})
