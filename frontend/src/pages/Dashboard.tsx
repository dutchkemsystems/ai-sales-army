import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import {
  Users, Send, Calendar, TrendingUp, ArrowUpRight,
  BarChart3, Clock, Target
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line
} from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [performance, setPerformance] = useState<any[]>([])
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [analyticsRes, perfRes, recsRes] = await Promise.all([
        api.analytics.pipeline(),
        api.analytics.performance(),
        api.analytics.recommendations(),
      ])
      setAnalytics(analyticsRes)
      setPerformance(perfRes.agents || [])
      setRecommendations(recsRes.recommendations || [])
    } catch (err) {
      console.error('Failed to load dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" /></div>
  }

  const funnelData = [
    { name: 'Discovered', value: analytics?.total_leads || 0 },
    { name: 'Researched', value: analytics?.researched || 0 },
    { name: 'Personalized', value: analytics?.personalized || 0 },
    { name: 'Outreach Sent', value: analytics?.outreach_sent || 0 },
    { name: 'Replied', value: analytics?.replied || 0 },
    { name: 'Meetings', value: analytics?.meetings_booked || 0 },
    { name: 'Closed', value: analytics?.closed_won || 0 },
  ]

  const agentData = performance.map((p: any) => ({
    name: p.agent_name,
    success: p.success_rate || 0,
    processed: p.leads_processed || 0,
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <button onClick={loadData} className="btn-secondary">Refresh</button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Leads', value: analytics?.total_leads || 0, icon: Users, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Outreach Sent', value: analytics?.outreach_sent || 0, icon: Send, color: 'text-green-600', bg: 'bg-green-50' },
          { label: 'Meetings Booked', value: analytics?.meetings_booked || 0, icon: Calendar, color: 'text-purple-600', bg: 'bg-purple-50' },
          { label: 'Conversion Rate', value: `${(analytics?.conversion_rate || 0).toFixed(1)}%`, icon: TrendingUp, color: 'text-amber-600', bg: 'bg-amber-50' },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
              </div>
              <div className={`p-3 rounded-lg ${bg}`}>
                <Icon className={`w-6 h-6 ${color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Funnel */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Pipeline Funnel</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnelData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Agent Performance */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agentData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="success" fill="#22c55e" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recommendations */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          <Target className="w-5 h-5 inline mr-2" />
          AI Recommendations
        </h2>
        <div className="space-y-3">
          {recommendations.length === 0 ? (
            <p className="text-gray-500">No recommendations at this time. Start by discovering leads!</p>
          ) : (
            recommendations.map((rec: any, i: number) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                <ArrowUpRight className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-gray-900">{rec.title || rec.action}</p>
                  <p className="text-sm text-gray-500">{rec.description || rec.reason}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card text-center">
          <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Avg. Time to Book</p>
          <p className="text-xl font-bold">{(analytics?.avg_time_to_book || 0).toFixed(1)} days</p>
        </div>
        <div className="card text-center">
          <BarChart3 className="w-8 h-8 text-green-500 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Revenue Forecast</p>
          <p className="text-xl font-bold">${(analytics?.revenue_forecast || 0).toLocaleString()}</p>
        </div>
        <div className="card text-center">
          <Users className="w-8 h-8 text-purple-500 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Interested Leads</p>
          <p className="text-xl font-bold">{analytics?.interested || 0}</p>
        </div>
      </div>
    </div>
  )
}
