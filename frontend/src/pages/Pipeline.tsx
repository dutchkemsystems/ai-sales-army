import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { GripVertical, User, Mail, Phone, Building2 } from 'lucide-react'

const stages = [
  { key: 'discovered', label: 'Discovered', color: 'bg-blue-100 border-blue-300' },
  { key: 'researched', label: 'Researched', color: 'bg-yellow-100 border-yellow-300' },
  { key: 'personalized', label: 'Personalized', color: 'bg-purple-100 border-purple-300' },
  { key: 'outreach_sent', label: 'Outreach Sent', color: 'bg-cyan-100 border-cyan-300' },
  { key: 'following_up', label: 'Following Up', color: 'bg-orange-100 border-orange-300' },
  { key: 'interested', label: 'Interested', color: 'bg-green-100 border-green-300' },
  { key: 'meeting_booked', label: 'Meeting Booked', color: 'bg-emerald-100 border-emerald-300' },
]

export default function Pipeline() {
  const [leads, setLeads] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadLeads() }, [])

  const loadLeads = async () => {
    try {
      const res = await api.leads.list({ limit: 500 })
      setLeads(res.leads || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const getLeadsForStage = (stage: string) => leads.filter(l => l.status === stage)

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" /></div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
        <button onClick={loadLeads} className="btn-secondary">Refresh</button>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {stages.map(({ key, label, color }) => {
          const stageLeads = getLeadsForStage(key)
          return (
            <div key={key} className="flex-shrink-0 w-72">
              <div className={`rounded-lg border-2 ${color} p-3 mb-3`}>
                <h3 className="font-semibold text-gray-800">{label}</h3>
                <p className="text-sm text-gray-600">{stageLeads.length} leads</p>
              </div>
              <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                {stageLeads.map(lead => (
                  <div key={lead.id} className="bg-white border border-gray-200 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-primary-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{lead.lead_first_name} {lead.lead_last_name}</p>
                        <p className="text-xs text-gray-500">{lead.lead_title}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Building2 className="w-3 h-3" />
                      <span>{lead.company_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                      <Mail className="w-3 h-3" />
                      <span className="truncate">{lead.lead_email}</span>
                    </div>
                    <div className="mt-2">
                      <span className={`badge ${lead.score === 'high' ? 'badge-success' : lead.score === 'medium' ? 'badge-warning' : 'badge-danger'}`}>
                        {lead.score}
                      </span>
                    </div>
                  </div>
                ))}
                {stageLeads.length === 0 && (
                  <div className="text-center py-8 text-gray-400 text-sm">No leads</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
