'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface BarChartWidgetProps {
  data: { label: string; value: number }[]
  color?: string
  layout?: 'horizontal' | 'vertical'
}

const PALETTE = ['#58B9AF', '#3fa69c', '#7ddbd3', '#C1DEDB', '#2d8b82']
const PALETTE_WARM = ['#353A3A', '#454c4c', '#5e6666', '#7a8282', '#2a2e2e']

const formatValue = (value: number) => {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toFixed(0)}`
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-900/95 backdrop-blur-md px-4 py-3 rounded-xl shadow-lg border border-white/10">
      <p className="text-[11px] font-semibold text-surface-300 mb-1">{label || payload[0]?.payload?.label}</p>
      <p className="text-sm text-white font-bold">{formatValue(payload[0].value)}</p>
    </div>
  )
}

export default function BarChartWidget({
  data,
  color = '#58B9AF',
  layout = 'vertical',
}: BarChartWidgetProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnée disponible
      </div>
    )
  }

  const isWarm = color.startsWith('#f') || color.startsWith('#e') || color.startsWith('#c')
  const palette = isWarm ? PALETTE_WARM : PALETTE

  if (layout === 'horizontal') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
          <XAxis type="number" tickFormatter={formatValue} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} width={90} tickLine={false} axisLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(88, 185, 175, 0.04)' }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((_, i) => (
              <Cell key={i} fill={palette[i % palette.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} />
        <YAxis tickFormatter={formatValue} tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} width={55} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(88, 185, 175, 0.04)' }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} barSize={28}>
          {data.map((_, i) => (
            <Cell key={i} fill={palette[i % palette.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
