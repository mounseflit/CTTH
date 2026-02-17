import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between px-2 py-3">
      <p className="text-xs font-medium text-surface-400">
        Page {page} sur {totalPages}
      </p>
      <div className="flex gap-1.5">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="w-8 h-8 flex items-center justify-center text-sm border border-surface-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-50 hover:border-surface-300 transition-all"
        >
          <ChevronLeft size={14} />
        </button>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="w-8 h-8 flex items-center justify-center text-sm border border-surface-200 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-surface-50 hover:border-surface-300 transition-all"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}
