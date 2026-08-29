import React from 'react'
import './Pagination.css'

interface PaginationProps {
  page: number
  hasMore: boolean
  onPrev: () => void
  onNext: () => void
  loading?: boolean
}

const Pagination: React.FC<PaginationProps> = ({ page, hasMore, onPrev, onNext, loading = false }) => {
  if (page === 1 && !hasMore) return null

  return (
    <div className="pn-pagination">
      <button
        className="pn-btn pn-btn-ghost"
        onClick={onPrev}
        disabled={page <= 1 || loading}
      >
        Previous
      </button>
      <span className="pn-pagination-page">Page {page}</span>
      <button
        className="pn-btn pn-btn-ghost"
        onClick={onNext}
        disabled={!hasMore || loading}
      >
        Next
      </button>
    </div>
  )
}

export default Pagination