'use client'

interface BarChartWidgetProps {
  data: { label: string; value: number }[]
  color?: string
  layout?: 'horizontal' | 'vertical'
}

const PALETTE = ['#58B9AF', '#3fa69c', '#7ddbd3', '#C1DEDB', '#2d8b82']

function fmt(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

export default function BarChartWidget({
  data,
  color,
  layout = 'vertical',
}: BarChartWidgetProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnée disponible
      </div>
    )
  }

  if (layout === 'horizontal') {
    // Horizontal bar chart (label on left, bar grows right)
    const maxVal = Math.max(...data.map((d) => d.value), 1)
    const barH = 28
    const gap = 8
    const labelW = 100
    const padR = 60
    const padT = 8
    const W = 560
    const barW = W - labelW - padR
    const H = padT + data.length * (barH + gap)

    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: Math.max(H, 120) }}>
        {data.map((d, i) => {
          const y = padT + i * (barH + gap)
          const w = (d.value / maxVal) * barW
          const barColor = color || PALETTE[i % PALETTE.length]
          return (
            <g key={i}>
              {/* Label */}
              <text
                x={labelW - 8}
                y={y + barH / 2 + 4}
                textAnchor="end"
                fontSize="11"
                fill="#64748b"
              >
                {d.label.length > 14 ? d.label.slice(0, 13) + '…' : d.label}
              </text>
              {/* Bar background */}
              <rect x={labelW} y={y} width={barW} height={barH} rx="6" fill="#f0f3f3" />
              {/* Bar fill */}
              <rect x={labelW} y={y} width={Math.max(w, 4)} height={barH} rx="6" fill={barColor} />
              {/* Value label */}
              <text
                x={labelW + Math.max(w, 4) + 6}
                y={y + barH / 2 + 4}
                fontSize="10"
                fill="#94a3b8"
              >
                {fmt(d.value)}
              </text>
            </g>
          )
        })}
      </svg>
    )
  }

  // Vertical bar chart
  const maxVal = Math.max(...data.map((d) => d.value), 1)
  const W = 560
  const H = 240
  const padL = 60
  const padR = 12
  const padT = 16
  const padB = 36
  const chartW = W - padL - padR
  const chartH = H - padT - padB
  const barW = Math.min(36, (chartW / data.length) * 0.6)
  const slotW = chartW / data.length

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    v: maxVal * t,
    y: padT + chartH - t * chartH,
  }))

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 260 }}>
      {/* Grid + Y ticks */}
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={t.y} x2={W - padR} y2={t.y} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 3" />
          <text x={padL - 6} y={t.y + 4} textAnchor="end" fontSize="10" fill="#94a3b8">
            {fmt(t.v)}
          </text>
        </g>
      ))}

      {/* Bars */}
      {data.map((d, i) => {
        const x = padL + i * slotW + (slotW - barW) / 2
        const barH2 = (d.value / maxVal) * chartH
        const y = padT + chartH - barH2
        const barColor = color || PALETTE[i % PALETTE.length]
        return (
          <g key={i}>
            <rect x={x} y={y} width={barW} height={Math.max(barH2, 2)} rx="5" fill={barColor} />
            <text
              x={x + barW / 2}
              y={H - 6}
              textAnchor="middle"
              fontSize="10"
              fill="#94a3b8"
            >
              {d.label.length > 8 ? d.label.slice(0, 7) + '…' : d.label}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
