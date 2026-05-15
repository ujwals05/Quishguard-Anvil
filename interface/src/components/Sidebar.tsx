import { LayoutDashboard, Activity, Search, Shield, Settings,  User } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const menuItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Activity, label: 'Workflow Trace', path: '/workflow' },
    { icon: Search, label: 'Investigation', path: '/investigation' },
    { icon: Shield, label: 'Security Assets', path: '/assets' },
  ];

  return (
    <aside className="w-64 h-screen bg-surface-container border-r border-outline-variant flex flex-col fixed left-0 top-0 z-50">
      <div className="p-6 flex items-center gap-3">

        <span className="text-xl font-bold tracking-tight">QuishGuard</span>
      </div>

      <nav className="flex-1 px-4 py-6 space-y-2">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                ? 'bg-primary/10 text-primary'
                : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-outline-variant space-y-2">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface rounded-lg transition-all">
          <Settings className="w-5 h-5" />
          <span className="font-medium text-sm">Settings</span>
        </button>
        <div className="flex items-center gap-3 px-4 py-3 mt-4 bg-surface-container-low rounded-xl border border-outline-variant/30">
          <div className="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center border border-outline-variant">
            <User className="w-5 h-5 text-primary" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold truncate">Analyst-01</span>
            <span className="text-xs text-on-surface-variant">L3 Response</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
