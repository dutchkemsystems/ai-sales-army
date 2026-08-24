import { useState } from 'react'
import { api } from '../utils/api'
import { Brain, BarChart3, Clock, Users, MessageSquare, Webhook, Zap } from 'lucide-react'

export default function Insights() {
  const [activeTab, setActiveTab] = useState('sentiment')
  const [sentimentText, setSentimentText] = useState('')
  const [sentimentResult, setSentimentResult] = useState<any>(null)
  const [intentText, setIntentText] = useState('')
  const [intentResult, setIntentResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const tabs = [
    { key: 'sentiment', label: 'Sentiment', icon: Brain },
    { key: 'intent', label: 'Intent', icon: Zap },
    { key: 'sendtime', label: 'Send Time', icon: Clock },
    { key: 'crm', label: 'CRM', icon: Users },
    { key: 'conversations', label: 'Conversations', icon: MessageSquare },
    { key: 'webhooks', label: 'Webhooks', icon: Webhook },
  ]

  const analyzeSentiment = async () => {
    if (!sentimentText) return
    setLoading(true)
    try {
      const res = await fetch(`/api/sentiment/analyze?text=${encodeURIComponent(sentimentText)}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      setSentimentResult(await res.json())
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  const detectIntent = async () => {
    if (!intentText) return
    setLoading(true)
    try {
      const res = await fetch(`/api/intent/detect?text=${encodeURIComponent(intentText)}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      setIntentResult(await res.json())
    } catch (err) { console.error(err) }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">AI Insights & Tools</h1>

      <div className="flex gap-2 flex-wrap">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === key ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}>
            <Icon className="w-4 h-4" />{label}
          </button>
        ))}
      </div>

      {activeTab === 'sentiment' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Sentiment Analysis</h2>
          <p className="text-sm text-gray-500">Analyze email replies and messages using local HuggingFace model</p>
          <textarea className="input-field" rows={4} placeholder="Paste a reply message to analyze..." value={sentimentText} onChange={e => setSentimentText(e.target.value)} />
          <button onClick={analyzeSentiment} disabled={loading} className="btn-primary">{loading ? 'Analyzing...' : 'Analyze Sentiment'}</button>
          {sentimentResult && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className={`badge ${sentimentResult.sentiment === 'positive' ? 'badge-success' : sentimentResult.sentiment === 'negative' ? 'badge-danger' : 'badge-warning'}`}>
                  {sentimentResult.sentiment?.toUpperCase()}
                </span>
                <span className="text-sm text-gray-500">Confidence: {(sentimentResult.confidence * 100).toFixed(1)}%</span>
              </div>
              {sentimentResult.should_escalate && <p className="text-sm text-red-600">⚠ Should escalate to human - negative sentiment detected</p>}
              {sentimentResult.is_interested && <p className="text-sm text-green-600">✓ Lead shows interest - consider scheduling meeting</p>}
            </div>
          )}
        </div>
      )}

      {activeTab === 'intent' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Intent Detection</h2>
          <p className="text-sm text-gray-500">Detect buying signals, urgency, budget, and decision-maker intent</p>
          <textarea className="input-field" rows={4} placeholder="Paste text to detect intent..." value={intentText} onChange={e => setIntentText(e.target.value)} />
          <button onClick={detectIntent} disabled={loading} className="btn-primary">{loading ? 'Detecting...' : 'Detect Intent'}</button>
          {intentResult && (
            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
              <div className="flex items-center gap-2">
                <span className="badge badge-info">{intentResult.primary_intent}</span>
                <span className="text-sm text-gray-500">Confidence: {(intentResult.confidence * 100).toFixed(1)}%</span>
              </div>
              <p className="text-sm font-medium">Recommended Action: <span className="text-primary-600">{intentResult.recommended_action}</span></p>
              {intentResult.should_escalate && <p className="text-sm text-red-600">⚠ High intent detected - escalate to sales team</p>}
              {intentResult.all_intents && Object.keys(intentResult.all_intents).length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {Object.entries(intentResult.all_intents).map(([intent, data]: [string, any]) => (
                    <span key={intent} className="badge bg-gray-100 text-gray-700">{intent}: {(data.score * 100).toFixed(0)}%</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'sendtime' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Smart Send-Time Optimization</h2>
          <p className="text-sm text-gray-500">AI-powered optimal send time prediction based on engagement patterns</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium mb-2">Email Best Times</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Tuesday 9:00 AM</span><span className="badge badge-success">Best</span></div>
                <div className="flex justify-between"><span>Wednesday 10:00 AM</span><span className="badge badge-info">Good</span></div>
                <div className="flex justify-between"><span>Thursday 2:00 PM</span><span className="badge badge-info">Good</span></div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-medium mb-2">LinkedIn Best Times</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span>Tuesday 8:00 AM</span><span className="badge badge-success">Best</span></div>
                <div className="flex justify-between"><span>Wednesday 5:00 PM</span><span className="badge badge-info">Good</span></div>
                <div className="flex justify-between"><span>Thursday 7:00 AM</span><span className="badge badge-info">Good</span></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'crm' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Local CRM</h2>
          <p className="text-sm text-gray-500">Built-in CRM - no external API needed</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-blue-600">0</p>
              <p className="text-sm text-gray-600">Contacts</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-600">0</p>
              <p className="text-sm text-gray-600">Active Deals</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-purple-600">$0</p>
              <p className="text-sm text-gray-600">Pipeline Value</p>
            </div>
          </div>
          <p className="text-sm text-gray-500">CRM data syncs automatically from lead pipeline</p>
        </div>
      )}

      {activeTab === 'conversations' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Conversation Memory</h2>
          <p className="text-sm text-gray-500">Track full conversation context across all channels</p>
          <div className="text-center py-8 text-gray-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-3" />
            <p>Conversations will appear here as leads respond</p>
          </div>
        </div>
      )}

      {activeTab === 'webhooks' && (
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold">Webhook System</h2>
          <p className="text-sm text-gray-500">Event-driven notifications for lead activities</p>
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Available Events</h3>
            <div className="flex flex-wrap gap-2">
              {['lead.discovered', 'outreach.sent', 'outreach.replied', 'meeting.booked', 'deal.won'].map(event => (
                <span key={event} className="badge bg-blue-100 text-blue-700">{event}</span>
              ))}
            </div>
          </div>
          <p className="text-sm text-gray-500">Configure webhooks via API to receive real-time notifications</p>
        </div>
      )}
    </div>
  )
}
