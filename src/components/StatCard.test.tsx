import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import StatCard from './StatCard'

describe('StatCard', () => {
  it('labels the region with the title so screen readers can tell the cards apart', () => {
    render(<StatCard title="Active leases" value={12} />)
    expect(screen.getByRole('region', { name: 'Active leases' })).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('renders the icon the dashboards pass in', () => {
    const { container } = render(<StatCard title="Units" value={4} icon="🏠" />)
    expect(container.textContent).toContain('🏠')
  })

  it('shows a skeleton placeholder instead of the value while loading', () => {
    const { container } = render(<StatCard title="Units" value={4} loading />)
    expect(container.querySelector('.skeleton')).toBeInTheDocument()
    expect(screen.queryByText('4')).not.toBeInTheDocument()
  })

  it('colour-codes the trend by direction', () => {
    render(<StatCard title="Revenue" value={1000} trend={{ value: '+8%', positive: true }} />)
    expect(screen.getByText('+8%')).toHaveStyle({ color: 'var(--success)' })

    render(<StatCard title="Vacancies" value={3} trend={{ value: '+2%', positive: false }} />)
    expect(screen.getByText('+2%')).toHaveStyle({ color: 'var(--danger)' })
  })

  it('omits the subtitle row when there is nothing to say', () => {
    render(<StatCard title="Leads" value={0} />)
    expect(screen.getByText('Leads')).toBeInTheDocument()
    expect(screen.queryByText('undefined')).not.toBeInTheDocument()
  })
})
