const colorMap: Record<string, string> = {
  regulatory: 'bg-red-50 text-red-600 ring-red-100',
  market: 'bg-blue-50 text-blue-600 ring-blue-100',
  policy: 'bg-violet-50 text-violet-600 ring-violet-100',
  trade_agreement: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
  industry: 'bg-amber-50 text-amber-600 ring-amber-100',
  sustainability: 'bg-teal-50 text-teal-600 ring-teal-100',
  technology: 'bg-cyan-50 text-cyan-600 ring-cyan-100',
  // Status badges
  active: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
  error: 'bg-red-50 text-red-600 ring-red-100',
  rate_limited: 'bg-yellow-50 text-yellow-600 ring-yellow-100',
  maintenance: 'bg-surface-100 text-surface-600 ring-surface-200',
  pending: 'bg-yellow-50 text-yellow-600 ring-yellow-100',
  generating: 'bg-blue-50 text-blue-600 ring-blue-100',
  completed: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
  failed: 'bg-red-50 text-red-600 ring-red-100',
}

const dotColorMap: Record<string, string> = {
  regulatory: 'bg-red-400',
  market: 'bg-blue-400',
  policy: 'bg-violet-400',
  trade_agreement: 'bg-emerald-400',
  industry: 'bg-amber-400',
  sustainability: 'bg-teal-400',
  technology: 'bg-cyan-400',
  active: 'bg-emerald-400',
  error: 'bg-red-400',
  rate_limited: 'bg-yellow-400',
  maintenance: 'bg-surface-400',
  pending: 'bg-yellow-400',
  generating: 'bg-blue-400',
  completed: 'bg-emerald-400',
  failed: 'bg-red-400',
}

const labelMap: Record<string, string> = {
  regulatory: 'Réglementaire',
  market: 'Marché',
  policy: 'Politique',
  trade_agreement: 'Accord commercial',
  industry: 'Industrie',
  sustainability: 'Durabilité',
  technology: 'Technologie',
  active: 'Actif',
  error: 'Erreur',
  rate_limited: 'Limité',
  maintenance: 'Maintenance',
  pending: 'En attente',
  generating: 'En cours',
  completed: 'Terminé',
  failed: 'Échoué',
}

interface BadgeProps {
  type: string
  label?: string
}

export default function Badge({ type, label }: BadgeProps) {
  const colors = colorMap[type] || 'bg-surface-100 text-surface-600 ring-surface-200'
  const dotColor = dotColorMap[type] || 'bg-surface-400'
  const displayLabel = label || labelMap[type] || type

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-semibold uppercase tracking-wider ring-1 ring-inset ${colors}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {displayLabel}
    </span>
  )
}
