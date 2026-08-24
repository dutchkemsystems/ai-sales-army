import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Plus, Send, Pause, Play, Trash2 } from 'lucide-react'

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', channels: ['email'] })

  useEffect(() => { loadCampaigns() }, [])

  const loadCampaigns = async () => {
    try {
      const res = await api.leads.list({ limit: 100 })
      setCampaigns([])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  const handleCreate = async () => {
    try {
      await api.campaigns.create(form)
      setShowCreate(false)
      setForm({ name: '', description: '', channels: ['email'] })
    } catch (err) { console.error(err) }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
        <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" /> New Campaign
        </button>
      </div>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg space-y-4">
            <h2 className="text-lg font-semibold">Create Campaign</h2>
            <input className="input-field" placeholder="Campaign name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            <textarea className="input-field" placeholder="Description" rows={3} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            <div>
              <label className="text-sm font-medium text-gray-700">Channels</label>
              <div className="flex gap-3 mt-2">
                {['email', 'linkedin', 'twitter', 'sms'].map(ch => (
                  <label key={ch} className="flex items-center gap-2">
                    <input type="checkbox" checked={form.channels.includes(ch)} onChange={e => {
                      setForm({ ...form, channels: e.target.checked ? [...form.channels, ch] : form.channels.filter(c => c !== ch) })
                    }} className="rounded" />
                    <span className="text-sm capitalize">{ch}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleCreate} className="btn-primary">Create</button>
            </div>
          </div>
        </div>
      )}

      <div className="card text-center py-12 text-gray-500">
        <Send className="w-12 h-12 mx-auto mb-4 text-gray-300" />
        <p className="text-lg font-medium text-gray-700 mb-2">No campaigns yet</p>
        <p className="text-sm">Create your first campaign to start outreach.</p>
      </div>
    </div>
  )
}
