'use client'

interface PieChartWidgetProps {
  data: { label: string; value: number }[]
  colors?: string[]
}

const DEFAULT_COLORS = [
  '#3fa69c', '#f05e06', '#6366f1', '#ec4899', '#f59e0b',
  '#10b981', '#8b5cf6', '#ef4444', '#06b6d4', '#84cc16',
  '#353A3A', '#d946ef', '#0ea5e9', '#f97316', '#14b8a6',
]

function fmtValue(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return value.toFixed(1)
}

export default function PieChartWidget({
  data,
  colors = DEFAULT_COLORS,
}: PieChartWidgetProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnée disponible
      </div>
    )
  }

  const total = data.reduce((s, d) => s + d.value, 0) || 1

  // Group slices < 3% into "Autres"
  const threshold = 0.03
  const mainSlices: { label: string; value: number }[] = []
  let othersValue = 0
  data.forEach(d => {
    if (d.value / total < threshold) {
      othersValue += d.value
    } else {
      mainSlices.push(d)
    }
  })
  if (othersValue > 0) {
    mainSlices.push({ label: 'Autres', value: othersValue })
  }

  // Sort descending
  mainSlices.sort((a, b) => b.value - a.value)

  const CX = 100
  const CY = 100
  const R = 85
  const innerR = 50

  // Build arc paths
  let cumAngle = -Math.PI / 2
  const slices = mainSlices.map((d, i) => {
    const angle = (d.value / total) * 2 * Math.PI
    const startAngle = cumAngle
    const endAngle = cumAngle + angle
    cumAngle = endAngle

    const x1 = CX + R * Math.cos(startAngle)
    const y1 = CY + R * Math.sin(startAngle)
    const x2 = CX + R * Math.cos(endAngle)
    const y2 = CY + R * Math.sin(endAngle)
    const ix1 = CX + innerR * Math.cos(startAngle)
    const iy1 = CY + innerR * Math.sin(startAngle)
    const ix2 = CX + innerR * Math.cos(endAngle)
    const iy2 = CY + innerR * Math.sin(endAngle)
    const large = angle > Math.PI ? 1 : 0
    const pct = ((d.value / total) * 100).toFixed(1)

    const path = [
      `M ${ix1} ${iy1}`,
      `L ${x1} ${y1}`,
      `A ${R} ${R} 0 ${large} 1 ${x2} ${y2}`,
      `L ${ix2} ${iy2}`,
      `A ${innerR} ${innerR} 0 ${large} 0 ${ix1} ${iy1}`,
      'Z',
    ].join(' ')

    return { path, color: colors[i % colors.length], label: d.label, pct, value: d.value }
  })

  return (
    <div className="w-full flex flex-col items-center gap-4">
      {/* Donut Chart */}
      <svg viewBox="0 0 200 200" className="w-full" style={{ maxWidth: 240, height: 240 }}>
        {/* Donut slices */}
        {slices.map((s, i) => (
          <path key={i} d={s.path} fill={s.color} stroke="#fff" strokeWidth="2" />
        ))}

        {/* Center label */}
        <text x={CX} y={CY - 6} textAnchor="middle" fontSize="10" fill="#94a3b8">Total</text>
        <text x={CX} y={CY + 12} textAnchor="middle" fontSize="14" fontWeight="700" fill="#2a2f2f">
          {fmtValue(total)}
        </text>
      </svg>

      {/* Legend - below chart, wrapping rows */}
      <div className="w-full grid grid-cols-1 gap-2">
        {slices.map((s, i) => (
          <div
            key={i}
            className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-surface-50 transition-colors"
          >
            <span
              className="w-3 h-3 rounded-sm flex-shrink-0"
              style={{ backgroundColor: s.color }}
            />
            <span className="text-xs text-surface-600 truncate flex-1" title={s.label}>
              {s.label}
            </span>
            <span className="text-xs font-semibold text-surface-800 flex-shrink-0 ml-auto">
              {s.pct}%
            </span>
            <span className="text-[10px] text-surface-400 flex-shrink-0 w-14 text-right">
              {fmtValue(s.value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
