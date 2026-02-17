'use client'

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import type { TrendDataPoint } from '@/types'

interface AreaTrendChartProps {
  data: TrendDataPoint[]
}

const formatValue = (value: number) => {
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`
  return value.toFixed(0)
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-900/95 backdrop-blur-md px-4 py-3 rounded-xl shadow-lg border border-white/10">
      <p className="text-[11px] font-semibold text-surface-300 mb-1.5">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-white/70">{entry.name}:</span>
          <span className="text-white font-bold">${formatValue(entry.value)}</span>
        </div>
      ))}
    </div>
  )
}

export default function AreaTrendChart({ data }: AreaTrendChartProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnée disponible
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gradExports" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#58B9AF" stopOpacity={0.25} />
            <stop offset="100%" stopColor="#58B9AF" stopOpacity={0.01} />
          </linearGradient>
          <linearGradient id="gradImports" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#353A3A" stopOpacity={0.2} />
            <stop offset="100%" stopColor="#353A3A" stopOpacity={0.01} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickLine={false}
          axisLine={{ stroke: '#e2e8f0' }}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#94a3b8' }}
          tickFormatter={formatValue}
          tickLine={false}
          axisLine={false}
          width={55}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: '12px', paddingTop: '12px' }}
        />
        <Area
          type="monotone"
          dataKey="exports"
          name="Exportations"
          stroke="#58B9AF"
          fillOpacity={1}
          fill="url(#gradExports)"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 5, fill: '#58B9AF', stroke: '#fff', strokeWidth: 2 }}
        />
        <Area
          type="monotone"
          dataKey="imports"
          name="Importations"
          stroke="#353A3A"
          fillOpacity={1}
          fill="url(#gradImports)"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 5, fill: '#353A3A', stroke: '#fff', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
