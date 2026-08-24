import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Search, Filter, Plus, ExternalLink, Mail, Linkedin, Star } from 'lucide-react'

const statusColors: Record<string, string> = {
  discovered: 'badge-info',
  researched: 'badge-warning',
  personalized: 'badge-success',
  outreach_sent: 'badge-info',
  following_up: 'badge-warning',
  interested: 'badge-success',
  meeting_booked: 'badge-success',
  lost: 'badge-danger',
}

export default function Leads() {
  const [leads, setLeads] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showDiscover, setShowDiscover] = useState(false)
  const [discoverForm, setDiscoverForm] = useState({ linkedin_query: '', apollo_query: '', industry: '', company_size: '', location: '' })
  const [discovering, setDiscovering] = useState(false)

  useEffect(() => { loadLeads() }, [statusFilter])

  const loadLeads = async () => {
    try {
      const params: any = { limit: 200 }
      if (statusFilter) params.status = statusFilter
      const res = await api.leads.list(params)
      setLeads(res.leads || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const handleDiscover = async () => {
    setDiscovering(true)
    try {
      await api.leads.discover(discoverForm)
      setShowDiscover(false)
      setTimeout(loadLeads, 3000)
    } catch (err) { console.error(err) }
    finally { setDiscovering(false) }
  }

  const filteredLeads = leads.filter(l =>
    `${l.lead_first_name} ${l.lead_last_name} ${l.company_name} ${l.lead_email}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <button onClick={() => setShowDiscover(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> Discover Leads
        </button>
      </div>

      {/* Discover Modal */}
      {showDiscover && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg space-y-4">
            <h2 className="text-lg font-semibold">Discover New Leads</h2>
            <input className="input-field" placeholder="LinkedIn search query" value={discoverForm.linkedin_query} onChange={e => setDiscoverForm({ ...discoverForm, linkedin_query: e.target.value })} />
            <input className="input-field" placeholder="Apollo search query" value={discoverForm.apollo_query} onChange={e => setDiscoverForm({ ...discoverForm, apollo_query: e.target.value })} />
            <input className="input-field" placeholder="Industry (e.g., SaaS, Fintech)" value={discoverForm.industry} onChange={e => setDiscoverForm({ ...discoverForm, industry: e.target.value })} />
            <input className="input-field" placeholder="Company size (e.g., 51-200)" value={discoverForm.company_size} onChange={e => setDiscoverForm({ ...discoverForm, company_size: e.target.value })} />
            <input className="input-field" placeholder="Location" value={discoverForm.location} onChange={e => setDiscoverForm({ ...discoverForm, location: e.target.value })} />
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowDiscover(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleDiscover} disabled={discovering} className="btn-primary">
                {discovering ? 'Discovering...' : 'Start Discovery'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
          <input className="input-field pl-10" placeholder="Search leads..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="input-field w-48" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="discovered">Discovered</option>
          <option value="researched">Researched</option>
          <option value="personalized">Personalized</option>
          <option value="outreach_sent">Outreach Sent</option>
          <option value="following_up">Following Up</option>
          <option value="interested">Interested</option>
          <option value="meeting_booked">Meeting Booked</option>
          <option value="lost">Lost</option>
        </select>
      </div>

      {/* Leads Table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Name</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Company</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Title</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Email</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Score</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filteredLeads.map((lead) => (
              <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{lead.lead_first_name} {lead.lead_last_name}</div>
                </td>
                <td className="px-4 py-3 text-gray-600">{lead.company_name}</td>
                <td className="px-4 py-3 text-gray-600">{lead.lead_title}</td>
                <td className="px-4 py-3 text-gray-600">{lead.lead_email}</td>
                <td className="px-4 py-3">
                  <span className={`badge ${lead.score === 'high' ? 'badge-success' : lead.score === 'medium' ? 'badge-warning' : 'badge-danger'}`}>
                    {lead.score}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${statusColors[lead.status] || 'badge-info'}`}>{lead.status}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button className="p-1 hover:bg-gray-100 rounded" title="Research"><Star className="w-4 h-4 text-gray-400" /></button>
                    <button className="p-1 hover:bg-gray-100 rounded" title="Email"><Mail className="w-4 h-4 text-gray-400" /></button>
                    <button className="p-1 hover:bg-gray-100 rounded" title="LinkedIn"><Linkedin className="w-4 h-4 text-gray-400" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredLeads.length === 0 && (
          <div className="text-center py-12 text-gray-500">No leads found. Start by discovering leads!</div>
        )}
      </div>
    </div>
  )
}
