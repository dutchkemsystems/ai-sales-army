import { create } from 'zustand'

interface User {
  id: string
  email: string
  first_name?: string
  last_name?: string
}

interface AppState {
  user: User | null
  token: string | null
  sidebarOpen: boolean
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  toggleSidebar: () => void
  logout: () => void
}

export const useStore = create<AppState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  sidebarOpen: true,
  setUser: (user) => set({ user }),
  setToken: (token) => {
    if (token) localStorage.setItem('token', token)
    else localStorage.removeItem('token')
    set({ token })
  },
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, token: null })
  },
}))
