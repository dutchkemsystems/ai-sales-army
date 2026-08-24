import { useState } from 'react'
import { User, Mail, Bell, Key, Building } from 'lucide-react'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('profile')

  const tabs = [
    { key: 'profile', label: 'Profile', icon: User },
    { key: 'integrations', label: 'Integrations', icon: Key },
    { key: 'notifications', label: 'Notifications', icon: Bell },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      <div className="flex gap-6">
        {/* Tabs */}
        <div className="w-48 flex-shrink-0">
          <nav className="space-y-1">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === key ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <div className="card space-y-4">
              <h2 className="text-lg font-semibold">Profile Settings</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700">First Name</label>
                  <input className="input-field mt-1" defaultValue="John" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700">Last Name</label>
                  <input className="input-field mt-1" defaultValue="Doe" />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Email</label>
                <input className="input-field mt-1" type="email" defaultValue="john@example.com" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Company</label>
                <input className="input-field mt-1" defaultValue="Dutchkem Ventures" />
              </div>
              <button className="btn-primary">Save Changes</button>
            </div>
          )}

          {activeTab === 'integrations' && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Integrations</h2>
              {[
                { name: 'LinkedIn', description: 'Connect your LinkedIn account for lead discovery', connected: false },
                { name: 'SendGrid', description: 'Email sending service for outreach', connected: false },
                { name: 'Apollo', description: 'B2B database for lead discovery', connected: false },
                { name: 'Clearbit', description: 'Company enrichment and tech stack detection', connected: false },
                { name: 'Twilio', description: 'SMS sending for follow-ups', connected: false },
                { name: 'Google Calendar', description: 'Calendar integration for meeting booking', connected: false },
                { name: 'HubSpot', description: 'CRM sync for deal tracking', connected: false },
              ].map(integration => (
                <div key={integration.name} className="card flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">{integration.name}</h3>
                    <p className="text-sm text-gray-500">{integration.description}</p>
                  </div>
                  <button className={integration.connected ? 'btn-secondary' : 'btn-primary'}>
                    {integration.connected ? 'Connected' : 'Connect'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="card space-y-4">
              <h2 className="text-lg font-semibold">Notification Settings</h2>
              {[
                { label: 'New lead discovered', description: 'Get notified when new leads enter the pipeline' },
                { label: 'Lead replies', description: 'Get notified when a lead responds to outreach' },
                { label: 'Meeting booked', description: 'Get notified when a meeting is scheduled' },
                { label: 'Daily summary', description: 'Receive a daily pipeline summary report' },
                { label: 'Campaign completed', description: 'Get notified when a campaign finishes' },
              ].map(item => (
                <div key={item.label} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="font-medium text-gray-900">{item.label}</p>
                    <p className="text-sm text-gray-500">{item.description}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              ))}
              <button className="btn-primary">Save Preferences</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
