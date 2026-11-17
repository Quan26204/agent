
import {
  LayoutDashboard,
  MessageSquare,
  Bot,
  Workflow,
  ShieldCheck,
  ListTodo,
  Bell,
  Settings,
  PanelLeftClose,
} from "lucide-react";

const navigation = [
  {
    section: "WORKSPACE",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      { id: "chat", label: "Chat", icon: MessageSquare },
    ],
  },
  {
    section: "AUTOMATION",
    items: [
      { id: "agents", label: "Agents", icon: Bot },
      { id: "workflows", label: "Workflows", icon: Workflow },
      { id: "approvals", label: "Approvals", icon: ShieldCheck },
      { id: "tasks", label: "Tasks", icon: ListTodo },
      { id: "reminders", label: "Reminders", icon: Bell },
    ],
  },
];

function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">A</div>

        <div className="brand-text">
          <strong>ATO</strong>
          <span>Agent Control Center</span>
        </div>

        <button className="icon-button sidebar-collapse" title="Sidebar">
          <PanelLeftClose size={17} />
        </button>
      </div>

      <button
        className="workspace-selector"
        onClick={() => onNavigate("dashboard")}
      >
        <div className="workspace-avatar">L</div>
        <div className="workspace-info">
          <strong>Local Workspace</strong>
          <span>Personal environment</span>
        </div>
        <span className="workspace-chevron">⌄</span>
      </button>

      <nav className="sidebar-navigation">
        {navigation.map((group) => (
          <div className="nav-group" key={group.section}>
            <div className="nav-section-title">
              {group.section}
            </div>

            {group.items.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  className={`nav-item ${
                    activePage === item.id ? "active" : ""
                  }`}
                  onClick={() => onNavigate(item.id)}
                >
                  <Icon size={18} strokeWidth={1.8} />
                  <span>{item.label}</span>

                  {item.id === "approvals" && (
                    <span className="nav-indicator" />
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button className="nav-item" onClick={() => onNavigate("settings")}>
          <Settings size={18} />
          <span>Settings</span>
        </button>

        <div className="sidebar-user">
          <div className="user-avatar">U</div>
          <div className="user-info">
            <strong>Local User</strong>
            <span>Administrator</span>
          </div>
          <span className="online-dot" />
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
