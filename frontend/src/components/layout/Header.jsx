
import { Search, Bell, Command } from "lucide-react";

const pageTitles = {
  dashboard: "Dashboard",
  chat: "Chat",
  agents: "Agents",
  workflows: "Workflows",
  approvals: "Approvals",
  tasks: "Tasks",
  reminders: "Reminders",
  settings: "Settings",
};

function Header({ activePage }) {
  return (
    <header className="top-header">
      <div className="header-breadcrumb">
        <span>ATO</span>
        <span className="breadcrumb-separator">/</span>
        <strong>{pageTitles[activePage] || "Dashboard"}</strong>
      </div>

      <div className="header-actions">
        <div className="system-status">
          <span className="status-dot" />
          Local environment
        </div>

        <button className="header-search">
          <Search size={15} />
          <span>Search</span>
          <kbd>
            <Command size={11} /> K
          </kbd>
        </button>

        <button className="icon-button" title="Notifications">
          <Bell size={18} />
        </button>

        <div className="header-avatar">U</div>
      </div>
    </header>
  );
}

export default Header;
