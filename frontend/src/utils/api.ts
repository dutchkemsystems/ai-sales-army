const API_BASE = '/api'

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token')
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }
  const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

export const api = {
  auth: {
    login: (email: string, password: string) =>
      fetchAPI('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
    register: (data: { email: string; password: string; first_name: string; last_name: string }) =>
      fetchAPI('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  },
  leads: {
    list: (params?: { status?: string; score?: string; limit?: number }) => {
      const query = new URLSearchParams(params as any).toString()
      return fetchAPI(`/leads?${query}`)
    },
    get: (id: string) => fetchAPI(`/leads/${id}`),
    discover: (filters: any) =>
      fetchAPI('/leads/discover', { method: 'POST', body: JSON.stringify(filters) }),
    updateStatus: (id: string, status: string) =>
      fetchAPI(`/leads/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
    research: (id: string) =>
      fetchAPI(`/leads/${id}/research`, { method: 'POST' }),
    personalize: (id: string, channel: string, tone: string) =>
      fetchAPI(`/leads/${id}/personalize`, { method: 'POST', body: JSON.stringify({ channel, tone }) }),
    qualify: (id: string) =>
      fetchAPI(`/leads/${id}/qualify`, { method: 'POST' }),
    book: (id: string, data: any) =>
      fetchAPI(`/leads/${id}/book`, { method: 'POST', body: JSON.stringify(data) }),
  },
  campaigns: {
    create: (data: any) =>
      fetchAPI('/campaigns', { method: 'POST', body: JSON.stringify(data) }),
    send: (id: string) =>
      fetchAPI(`/campaigns/${id}/send`, { method: 'POST' }),
  },
  analytics: {
    pipeline: () => fetchAPI('/analytics/pipeline'),
    performance: () => fetchAPI('/analytics/performance'),
    funnel: () => fetchAPI('/analytics/funnel'),
    forecast: () => fetchAPI('/analytics/forecast'),
    winLoss: () => fetchAPI('/analytics/win-loss'),
    recommendations: () => fetchAPI('/analytics/recommendations'),
  },
  dashboard: () => fetchAPI('/dashboard'),
  meetings: {
    list: () => fetchAPI('/meetings'),
  },
}
