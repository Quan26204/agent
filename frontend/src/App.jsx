
import { useState } from "react";

import Sidebar from "./components/layout/Sidebar";
import Header from "./components/layout/Header";

import DashboardPage from "./pages/DashboardPage";
import ChatPage from "./pages/ChatPage";

import "./App.css";

function ComingSoon({ title }) {
  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">ATO WORKSPACE</div>
          <h1>{title}</h1>
          <p>This section will be connected to ATO in the next stage.</p>
        </div>
      </div>

      <div className="panel coming-soon">
        <div className="coming-soon-icon">✦</div>
        <h2>{title} is coming soon</h2>
        <p>
          The interface will be implemented using the existing backend
          APIs. No backend changes are required.
        </p>
      </div>
    </div>
  );
}

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  function renderPage() {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={setActivePage} />;

      case "chat":
        return <ChatPage />;

      case "agents":
        return <ComingSoon title="Agents" />;

      case "workflows":
        return <ComingSoon title="Workflows" />;

      case "approvals":
        return <ComingSoon title="Approvals" />;

      case "tasks":
        return <ComingSoon title="Tasks" />;

      case "reminders":
        return <ComingSoon title="Reminders" />;

      case "settings":
        return <ComingSoon title="Settings" />;

      default:
        return <DashboardPage onNavigate={setActivePage} />;
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <main className="main-area">
        <Header activePage={activePage} />
        <div className="page-container">
          {renderPage()}
        </div>
      </main>
    </div>
  );
}

export default App;
