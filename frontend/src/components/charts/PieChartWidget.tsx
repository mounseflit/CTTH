'use client'

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface PieChartWidgetProps {
  data: { label: string; value: number }[]
  colors?: string[]
}

const DEFAULT_COLORS = [
  '#58B9AF',
  '#3fa69c',
  '#7ddbd3',
  '#C1DEDB',
  '#2d8b82',
  '#353A3A',
  '#f05e06',
  '#6366f1',
  '#ec4899',
  '#f59e0b',
]

const formatValue = (value: number) => {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `${value.toFixed(1)}%`
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface-900/95 backdrop-blur-md px-4 py-3 rounded-xl shadow-lg border border-white/10">
      <p className="text-[11px] font-semibold text-surface-300 mb-1">
        {payload[0]?.name}
      </p>
      <p className="text-sm text-white font-bold">
        {formatValue(payload[0].value)}
      </p>
    </div>
  )
}

export default function PieChartWidget({
  data,
  colors = DEFAULT_COLORS,
}: PieChartWidgetProps) {
  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400 text-sm">
        Aucune donnee disponible
      </div>
    )
  }

  const chartData = data.map((d) => ({ name: d.label, value: d.value }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          stroke="none"
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={colors[i % colors.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value: string) => (
            <span className="text-xs text-surface-600">{value}</span>
          )}
          iconType="circle"
          iconSize={8}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
