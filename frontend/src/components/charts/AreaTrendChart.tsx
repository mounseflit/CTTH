'use client'

import type { TrendDataPoint } from '@/types'

interface AreaTrendChartProps {
  data: TrendDataPoint[]
}

function fmt(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

export default function AreaTrendChart({ data }: AreaTrendChartProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnée disponible
      </div>
    )
  }

  const W = 600
  const H = 220
  const padL = 60
  const padR = 16
  const padT = 16
  const padB = 32

  const chartW = W - padL - padR
  const chartH = H - padT - padB

  const allValues = data.flatMap((d) => [d.exports ?? 0, d.imports ?? 0])
  const maxVal = Math.max(...allValues, 1)

  const xStep = chartW / Math.max(data.length - 1, 1)

  const toX = (i: number) => padL + i * xStep
  const toY = (v: number) => padT + chartH - (v / maxVal) * chartH

  const polyline = (key: 'exports' | 'imports') =>
    data.map((d, i) => `${toX(i)},${toY(d[key] ?? 0)}`).join(' ')

  const area = (key: 'exports' | 'imports') => {
    const pts = data.map((d, i) => `${toX(i)},${toY(d[key] ?? 0)}`).join(' ')
    const last = data.length - 1
    return `${padL},${padT + chartH} ${pts} ${toX(last)},${padT + chartH}`
  }

  // Y axis ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => ({
    v: maxVal * t,
    y: padT + chartH - t * chartH,
  }))

  return (
    <div className="w-full">
      {/* Legend */}
      <div className="flex items-center gap-4 mb-3 px-2">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#58B9AF' }} />
          <span className="text-xs text-surface-500 font-medium">Exportations</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: '#353A3A' }} />
          <span className="text-xs text-surface-500 font-medium">Importations</span>
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 260 }}>
        <defs>
          <linearGradient id="gExp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#58B9AF" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#58B9AF" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="gImp" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#353A3A" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#353A3A" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={padL} y1={t.y} x2={W - padR} y2={t.y} stroke="#e2e8f0" strokeWidth="1" strokeDasharray="4 3" />
            <text x={padL - 6} y={t.y + 4} textAnchor="end" fontSize="10" fill="#94a3b8">
              {fmt(t.v)}
            </text>
          </g>
        ))}

        {/* Area fills */}
        <polygon points={area('exports')} fill="url(#gExp)" />
        <polygon points={area('imports')} fill="url(#gImp)" />

        {/* Lines */}
        <polyline points={polyline('exports')} fill="none" stroke="#58B9AF" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        <polyline points={polyline('imports')} fill="none" stroke="#353A3A" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

        {/* Dots + X labels */}
        {data.map((d, i) => (
          <g key={i}>
            <circle cx={toX(i)} cy={toY(d.exports ?? 0)} r="4" fill="#58B9AF" stroke="#fff" strokeWidth="2" />
            <circle cx={toX(i)} cy={toY(d.imports ?? 0)} r="4" fill="#353A3A" stroke="#fff" strokeWidth="2" />
            <text x={toX(i)} y={H - 6} textAnchor="middle" fontSize="11" fill="#94a3b8">
              {d.period}
            </text>
          </g>
        ))}
      </svg>
    </div>
  )
}
