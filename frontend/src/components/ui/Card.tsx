interface CardProps {
  title?: string
  subtitle?: string
  children: React.ReactNode
  className?: string
  noPadding?: boolean
}

export default function Card({ title, subtitle, children, className = '', noPadding = false }: CardProps) {
  return (
    <div className={`glass-card rounded-2xl overflow-hidden animate-fade-in ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-surface-100">
          <h3 className="text-sm font-bold text-surface-800 tracking-tight">{title}</h3>
          {subtitle && (
            <p className="text-[11px] text-surface-400 mt-0.5">{subtitle}</p>
          )}
        </div>
      )}
      <div className={noPadding ? '' : 'p-6'}>{children}</div>
    </div>
  )
}
