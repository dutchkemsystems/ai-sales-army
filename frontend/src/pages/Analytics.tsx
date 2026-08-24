import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']

export default function Analytics() {
  const [pipeline, setPipeline] = useState<any>(null)
  const [performance, setPerformance] = useState<any[]>([])
  const [funnel, setFunnel] = useState<any>(null)
  const [forecast, setForecast] = useState<any>(null)
  const [winLoss, setWinLoss] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    try {
      const [p, perf, f, fc, wl] = await Promise.all([
        api.analytics.pipeline(),
        api.analytics.performance(),
        api.analytics.funnel(),
        api.analytics.forecast(),
        api.analytics.winLoss(),
      ])
      setPipeline(p)
      setPerformance(perf.agents || [])
      setFunnel(f)
      setForecast(fc)
      setWinLoss(wl)
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" /></div>
  }

  const funnelData = funnel ? Object.entries(funnel).filter(([k]) => k !== 'total').map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v as number })) : []
  const perfData = performance.map(p => ({ name: p.agent_name, success: p.success_rate, processed: p.leads_processed }))
  const winLossData = winLoss ? [
    { name: 'Won', value: winLoss.won_count || 0 },
    { name: 'Lost', value: winLoss.lost_count || 0 },
  ] : []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics & Reporting</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-sm text-gray-500">Total Revenue Forecast</p>
          <p className="text-3xl font-bold text-green-600 mt-1">${(forecast?.total_forecast || 0).toLocaleString()}</p>
          <p className="text-xs text-gray-400 mt-1">Confidence: {forecast?.confidence_level || 'N/A'}</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Win Rate</p>
          <p className="text-3xl font-bold text-blue-600 mt-1">{winLoss?.win_rate || 0}%</p>
          <p className="text-xs text-gray-400 mt-1">{winLoss?.won_count || 0} won / {winLoss?.lost_count || 0} lost</p>
        </div>
        <div className="card text-center">
          <p className="text-sm text-gray-500">Avg. Time to Book</p>
          <p className="text-3xl font-bold text-purple-600 mt-1">{pipeline?.avg_time_to_book?.toFixed(1) || 0} days</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Conversion Funnel</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnelData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Agent Success Rate</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={perfData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={110} />
              <Tooltip />
              <Bar dataKey="success" fill="#22c55e" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Win/Loss Analysis</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={winLossData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                {winLossData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          {winLoss?.common_loss_reasons && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Common Loss Reasons</h3>
              <ul className="text-sm text-gray-500 space-y-1">
                {winLoss.common_loss_reasons.map((r: string, i: number) => <li key={i}>- {r}</li>)}
              </ul>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Revenue by Stage</h2>
          {forecast?.by_stage && (
            <div className="space-y-3">
              {Object.entries(forecast.by_stage).map(([stage, value]: [string, any]) => (
                <div key={stage} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700 capitalize">{stage.replace(/_/g, ' ')}</span>
                  <span className="text-sm font-bold text-gray-900">${(value || 0).toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
