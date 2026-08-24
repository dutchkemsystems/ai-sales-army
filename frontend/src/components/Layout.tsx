import { Outlet, Link, useLocation } from 'react-router-dom'
import { useStore } from '../store'
import {
  LayoutDashboard, Users, Send, GitBranch, BarChart3,
  Calendar, Settings, Menu, X, LogOut, Zap
} from 'lucide-react'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/leads', label: 'Leads', icon: Users },
  { path: '/campaigns', label: 'Campaigns', icon: Send },
  { path: '/pipeline', label: 'Pipeline', icon: GitBranch },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/meetings', label: 'Meetings', icon: Calendar },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Layout() {
  const location = useLocation()
  const { sidebarOpen, toggleSidebar, logout } = useStore()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-white border-r border-gray-200 transition-all duration-300 flex flex-col`}>
        <div className="p-4 flex items-center justify-between border-b border-gray-100">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-gray-900">AI Sales Army</span>
            </div>
          )}
          <button onClick={toggleSidebar} className="p-1 hover:bg-gray-100 rounded">
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                location.pathname === path
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-100">
          <button
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors w-full"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
