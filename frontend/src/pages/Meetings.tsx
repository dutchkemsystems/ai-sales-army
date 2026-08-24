import { useEffect, useState } from 'react'
import { api } from '../utils/api'
import { Calendar, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'

const statusIcons: Record<string, any> = {
  pending: <Clock className="w-4 h-4 text-yellow-500" />,
  confirmed: <CheckCircle className="w-4 h-4 text-green-500" />,
  cancelled: <XCircle className="w-4 h-4 text-red-500" />,
  completed: <CheckCircle className="w-4 h-4 text-blue-500" />,
}

export default function Meetings() {
  const [meetings, setMeetings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadMeetings() }, [])

  const loadMeetings = async () => {
    try {
      const res = await api.meetings.list()
      setMeetings(res.meetings || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full" /></div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Meetings</h1>
        <button onClick={loadMeetings} className="btn-secondary">Refresh</button>
      </div>

      {meetings.length === 0 ? (
        <div className="card text-center py-12">
          <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p className="text-lg font-medium text-gray-700 mb-2">No meetings scheduled</p>
          <p className="text-sm text-gray-500">Meetings will appear here when leads are qualified and booked.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {meetings.map(meeting => (
            <div key={meeting.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">{meeting.meeting_title}</h3>
                {statusIcons[meeting.status] || <AlertCircle className="w-4 h-4 text-gray-400" />}
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="w-4 h-4" />
                  <span>{new Date(meeting.scheduled_start).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>{new Date(meeting.scheduled_start).toLocaleTimeString()} - {new Date(meeting.scheduled_end).toLocaleTimeString()}</span>
                </div>
                <p className="text-gray-500">{meeting.lead_first_name} {meeting.lead_last_name}</p>
                <p className="text-gray-400">{meeting.lead_email}</p>
              </div>
              {meeting.calendar_link && (
                <a href={meeting.calendar_link} target="_blank" rel="noopener" className="mt-3 inline-block text-sm text-primary-600 hover:underline">
                  View in Calendar
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
