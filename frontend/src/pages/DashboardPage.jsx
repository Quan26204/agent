
import { useEffect, useState } from "react";
import {
  Activity,
  Bot,
  CheckCircle2,
  Clock3,
  ListTodo,
  RefreshCw,
  ArrowUpRight,
} from "lucide-react";

import { getPlans } from "../services/api";

function formatDate(value) {
  if (!value) return "—";

  return new Date(value).toLocaleString("vi-VN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }) {
  const labels = {
    pending_approval: "Pending approval",
    needs_clarification: "Needs clarification",
    approved: "Approved",
    queued: "Queued",
    running: "Running",
    completed: "Completed",
    failed: "Failed",
    rejected: "Rejected",
  };

  return (
    <span className={`status-badge status-${status || "unknown"}`}>
      <span className="badge-dot" />
      {labels[status] || status || "Unknown"}
    </span>
  );
}

function DashboardPage({ onNavigate }) {
  const [plans, setPlans] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const data = await getPlans({ limit: 100, offset: 0 });

      setPlans(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
      setError(
        "Cannot connect to ATO backend. Check that the backend is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const jobs = plans.flatMap((plan) =>
    (plan.jobs || []).map((job) => ({
      ...job,
      planTitle: plan.title,
      planId: plan.id,
    }))
  );

  const pendingPlans = plans.filter(
    (plan) => plan.status === "pending_approval"
  ).length;

  const completedJobs = jobs.filter(
    (job) => job.status === "completed"
  ).length;

  const runningJobs = jobs.filter(
    (job) => job.status === "running" || job.status === "queued"
  ).length;

  const agentNames = [
    ...new Set(jobs.map((job) => job.target_agent).filter(Boolean)),
  ];

  const recentPlans = plans.slice(0, 6);

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow">OVERVIEW</div>
          <h1>Welcome to ATO</h1>
          <p>
            Monitor your AI agents, workflows and automation activity.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={loadDashboard}
          disabled={loading}
        >
          <RefreshCw size={15} className={loading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <Activity size={18} />
          <span>{error}</span>
          <button onClick={loadDashboard}>Retry</button>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-top">
            <span>Total Plans</span>
            <div className="stat-icon purple">
              <ListTodo size={19} />
            </div>
          </div>
          <div className="stat-value">
            {loading ? "—" : total}
          </div>
          <div className="stat-caption">All recorded plans</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Pending Approvals</span>
            <div className="stat-icon orange">
              <Clock3 size={19} />
            </div>
          </div>
          <div className="stat-value">
            {loading ? "—" : pendingPlans}
          </div>
          <div className="stat-caption">Awaiting your decision</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Completed Jobs</span>
            <div className="stat-icon green">
              <CheckCircle2 size={19} />
            </div>
          </div>
          <div className="stat-value">
            {loading ? "—" : completedJobs}
          </div>
          <div className="stat-caption">Successfully completed</div>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Active / Queued Jobs</span>
            <div className="stat-icon blue">
              <Activity size={19} />
            </div>
          </div>
          <div className="stat-value">
            {loading ? "—" : runningJobs}
          </div>
          <div className="stat-caption">Currently active or waiting</div>
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel recent-panel">
          <div className="panel-heading">
            <div>
              <h2>Recent Plans</h2>
              <p>Latest activity from your orchestrator</p>
            </div>

            <button
              className="text-button"
              onClick={() => onNavigate("workflows")}
            >
              View all <ArrowUpRight size={15} />
            </button>
          </div>

          {loading ? (
            <div className="empty-state">Loading plans...</div>
          ) : recentPlans.length === 0 ? (
            <div className="empty-state">
              <ListTodo size={25} />
              <strong>No plans yet</strong>
              <span>Create a task through ATO Chat to get started.</span>
              <button
                className="primary-button"
                onClick={() => onNavigate("chat")}
              >
                Open Chat
              </button>
            </div>
          ) : (
            <div className="plan-list">
              {recentPlans.map((plan) => (
                <div className="plan-row" key={plan.id}>
                  <div className="plan-main">
                    <div className="plan-icon">
                      <ListTodo size={17} />
                    </div>

                    <div className="plan-info">
                      <strong>{plan.title || "Untitled plan"}</strong>
                      <span>{formatDate(plan.created_at)}</span>
                    </div>
                  </div>

                  <div className="plan-meta">
                    <span className="job-count">
                      {(plan.jobs || []).length} jobs
                    </span>
                    <StatusBadge status={plan.status} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel agents-panel">
          <div className="panel-heading">
            <div>
              <h2>Detected Agents</h2>
              <p>Agents referenced by recorded jobs</p>
            </div>
            <Bot size={19} className="muted-icon" />
          </div>

          {loading ? (
            <div className="empty-state">Loading...</div>
          ) : agentNames.length === 0 ? (
            <div className="empty-state compact">
              No agent activity recorded yet.
            </div>
          ) : (
            <div className="agent-list">
              {agentNames.map((name) => {
                const count = jobs.filter(
                  (job) => job.target_agent === name
                ).length;

                return (
                  <div className="agent-row" key={name}>
                    <div className="agent-avatar">
                      <Bot size={17} />
                    </div>
                    <div className="agent-info">
                      <strong>{name}</strong>
                      <span>{count} recorded jobs</span>
                    </div>
                    <span className="agent-configured">
                      Detected
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          <div className="agent-note">
            This list is based on plan history. It does not represent live
            agent health.
          </div>
        </section>
      </div>
    </div>
  );
}

export default DashboardPage;
