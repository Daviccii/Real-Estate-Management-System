import React from 'react'
import './Pagination.css'

interface PaginationProps {
  page: number
  hasMore: boolean
  onPrev: () => void
  onNext: () => void
  loading?: boolean
  /** Total pages, when known (from propertyService.count()). Omit to fall back to "Page N" only. */
  totalPages?: number
}

const Pagination: React.FC<PaginationProps> = ({ page, hasMore, onPrev, onNext, loading = false, totalPages }) => {
  if (page === 1 && !hasMore && (totalPages === undefined || totalPages <= 1)) return null

  const isLastPage = typeof totalPages === 'number' ? page >= totalPages : !hasMore

  return (
    <div className="pn-pagination">
      <button
        className="pn-btn pn-btn-ghost"
        onClick={onPrev}
        disabled={page <= 1 || loading}
      >
        Previous
      </button>
      <span className="pn-pagination-page">
        {typeof totalPages === 'number' ? `Page ${page} of ${totalPages}` : `Page ${page}`}
      </span>
      <button
        className="pn-btn pn-btn-ghost"
        onClick={onNext}
        disabled={isLastPage || loading}
      >
        Next
      </button>
    </div>
  )
}

export default Pagination