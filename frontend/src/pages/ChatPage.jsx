
import { useEffect, useRef, useState } from "react";
import {
  Plus,
  Trash2,
  Send,
  MessageSquare,
  Sparkles,
  Check,
  X,
  Play,
  RefreshCw,
  Clock,
  Bot,
  AlertCircle,
} from "lucide-react";

import DocumentUpload from "../components/DocumentUpload";

const API_URL = "http://localhost:8000";

const PLAN_STATUS = {
  needs_clarification: "Needs clarification",
  pending_approval: "Pending approval",
  approved: "Approved",
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  rejected: "Rejected",
};

const JOB_STATUS = {
  awaiting_approval: "Awaiting approval",
  queued: "Queued",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
};

function isOrchestratorRequest(text) {
  const value = text.toLowerCase().trim();

  const reminderIntent =
    /\b(create|add|set|schedule|make)\s+(?:a\s+)?reminder\b/.test(value) ||
    /\bremind\s+me\b/.test(value) ||
    /\b(tạo|đặt|thêm|lập)\s+(?:một\s+)?(?:lời\s+)?nhắc\s*(?:nhở|việc)?\b/.test(value) ||
    /\bnhắc\s+(?:tôi|mình|tao|em|anh|chị)\b/.test(value);

  const taskIntent =
    /\b(create|add|make)\s+(?:a\s+)?task\b/.test(value) ||
    /\b(tạo|thêm|lập)\s+(?:một\s+)?task\b/.test(value);

  return reminderIntent || taskIntent;
}

async function readResponse(response) {
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail =
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail || data);

    throw new Error(detail || `Request failed (${response.status})`);
  }

  return data;
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }

  return String(value);
}

function PlanCard({ plan, busy, onAction, onRefresh }) {
  const status = plan.status || "unknown";
  const jobs = plan.jobs || [];

  return (
    <div className="orchestrator-card">
      <div className="orchestrator-card-header">
        <div className="orchestrator-card-title">
          <div className="orchestrator-icon">
            <Bot size={18} />
          </div>

          <div>
            <h3>{plan.title || "ATO Plan"}</h3>
            <span className={`plan-status status-${status}`}>
              {PLAN_STATUS[status] || status}
            </span>
          </div>
        </div>

        <button
          className="icon-button"
          onClick={() => onRefresh(plan.id)}
          disabled={busy}
          title="Refresh plan"
        >
          <RefreshCw size={15} />
        </button>
      </div>

      {plan.summary && (
        <p className="orchestrator-summary">{plan.summary}</p>
      )}

      {plan.clarification_questions?.length > 0 && (
        <div className="plan-clarification">
          <AlertCircle size={16} />
          <div>
            <strong>Additional information required</strong>
            {plan.clarification_questions.map((question, index) => (
              <p key={index}>{question}</p>
            ))}
          </div>
        </div>
      )}

      {jobs.length > 0 && (
        <div className="plan-jobs">
          <div className="plan-section-title">
            Proposed jobs ({jobs.length})
          </div>

          {jobs.map((job) => (
            <div className="plan-job" key={job.id || job.job_key}>
              <div className="plan-job-heading">
                <div>
                  <strong>{job.description || job.job_key}</strong>
                  <span className="plan-job-agent">
                    {job.target_agent} · {job.job_type}
                  </span>
                </div>

                <span className={`job-status status-${job.status}`}>
                  {JOB_STATUS[job.status] || job.status}
                </span>
              </div>

              {job.schedule &&
                Object.keys(job.schedule).length > 0 && (
                  <div className="plan-job-detail">
                    <Clock size={13} />
                    <span>{formatValue(job.schedule.datetime || job.schedule)}</span>
                  </div>
                )}

              {job.progress && job.progress.total > 0 && (
                <div className="plan-progress">
                  <div className="plan-progress-track">
                    <div
                      className="plan-progress-fill"
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(0, job.progress.percent || 0)
                        )}%`,
                      }}
                    />
                  </div>
                  <span>{job.progress.percent || 0}%</span>
                </div>
              )}

              {job.output && (
                <pre className="plan-job-output">
                  {formatValue(job.output)}
                </pre>
              )}

              {job.error && (
                <div className="plan-job-error">{job.error}</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="orchestrator-actions">
        {status === "pending_approval" && (
          <>
            <button
              className="plan-button plan-button-reject"
              onClick={() => onAction(plan.id, "reject")}
              disabled={busy}
            >
              <X size={15} />
              Reject
            </button>

            <button
              className="plan-button plan-button-approve"
              onClick={() => onAction(plan.id, "approve")}
              disabled={busy}
            >
              <Check size={15} />
              Approve
            </button>
          </>
        )}

        {status === "approved" && (
          <button
            className="plan-button plan-button-execute"
            onClick={() => onAction(plan.id, "execute")}
            disabled={busy}
          >
            <Play size={15} />
            Execute
          </button>
        )}

        {(status === "queued" || status === "running") && (
          <button
            className="plan-button plan-button-execute"
            onClick={() => onRefresh(plan.id)}
            disabled={busy}
          >
            <RefreshCw size={15} />
            Check progress
          </button>
        )}

        {busy && <span className="plan-action-loading">Processing...</span>}
      </div>

      {plan.message && (
        <p className="plan-response-message">{plan.message}</p>
      )}
    </div>
  );
}

function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [currentId, setCurrentId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [busyPlanId, setBusyPlanId] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function loadConversations() {
    try {
      const response = await fetch(`${API_URL}/conversations`);

      if (!response.ok) {
        throw new Error("Failed to load conversations");
      }

      const data = await response.json();
      setConversations(data);
    } catch (error) {
      console.error(error);
    }
  }

  
async function createConversation(
  title = "New conversation",
  resetMessages = true
) {
  const response = await fetch(`${API_URL}/conversations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });

  if (!response.ok) {
    throw new Error("Failed to create conversation");
  }

  const conversation = await response.json();
  
  console.log("[ATO] New conversation:", conversation);

  console.log("[ATO] Previous currentId:", currentId);

  console.log("[ATO] Reset messages:", resetMessages);

  setConversations((prev) => [
    conversation,
    ...prev.filter((item) => item.id !== conversation.id),
  ]);

  // Switch to the newly created conversation.
  setCurrentId(conversation.id);

  // Always start a new conversation with an empty message list.
  if (resetMessages) {
    setMessages([]);
    setInput("");
  }

  return conversation.id;
}


async function loadConversationMessages(id) {
  // Load conversation history and all Orchestrator plans.
  const [conversationResponse, plansResponse] = await Promise.all([
    fetch(`${API_URL}/conversations/${id}`),
    fetch(`${API_URL}/orchestrator/plans?limit=100&offset=0`),
  ]);

  if (!conversationResponse.ok) {
    throw new Error("Failed to load conversation");
  }

  const conversationData = await conversationResponse.json();

  // If plans cannot be loaded, keep the normal chat history available.
  let plansData = { items: [] };

  try {
    plansData = await readResponse(plansResponse);
  } catch (error) {
    console.error("Could not load Orchestrator plans:", error);
  }

  // Only restore plans belonging to the selected conversation.
  const conversationPlans = (plansData.items || [])
    .filter(
      (plan) =>
        String(plan.conversation_id) === String(id)
    )
    .sort((a, b) => {
      return new Date(a.created_at || 0) - new Date(b.created_at || 0);
    });

  // Reconstruct the original user request and its Plan Card.
  const restoredPlanMessages = conversationPlans.flatMap((plan) => [
    {
      role: "user",
      content: plan.user_request || plan.title || "ATO request",
    },
    {
      role: "assistant",
      type: "plan",
      plan,
    },
  ]);

  setCurrentId(id);

  console.log("[ATO] Loading conversation:", id);

  console.log(
    "[ATO] Restored plans:",
    conversationPlans.map((plan) => ({
      id: plan.id,
      conversation_id: plan.conversation_id,
      user_request: plan.user_request,
      status: plan.status,
    }))
  );
  
  // Normal chat messages + restored Orchestrator messages.
  setMessages([
    ...(conversationData.messages || []),
    ...restoredPlanMessages,
  ]);
}


  
async function selectConversation(id) {
  try {
    await loadConversationMessages(id);
  } catch (error) {
    console.error("Failed to restore conversation:", error);
    alert(`Could not load conversation: ${error.message}`);
  }
}


  async function deleteConversation(id) {
    try {
      const response = await fetch(
        `${API_URL}/conversations/${id}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Failed to delete conversation");
      }

      setConversations((prev) =>
        prev.filter((item) => item.id !== id)
      );

      if (String(currentId) === String(id)) {
        setCurrentId(null);
        setMessages([]);
        setInput("");
      }
    } catch (error) {
      console.error(error);
    }
  }

  function updatePlanMessage(plan) {
    setMessages((prev) =>
      prev.map((message) =>
        message.type === "plan" && message.plan?.id === plan.id
          ? { ...message, plan }
          : message
      )
    );
  }

  async function fetchPlan(planId) {
    const response = await fetch(
      `${API_URL}/orchestrator/plans/${planId}`
    );

    return readResponse(response);
  }

  async function refreshPlan(planId) {
    if (busyPlanId) return;

    setBusyPlanId(planId);

    try {
      const plan = await fetchPlan(planId);
      updatePlanMessage(plan);
    } catch (error) {
      console.error(error);
      alert(`Could not refresh plan: ${error.message}`);
    } finally {
      setBusyPlanId(null);
    }
  }

  async function pollPlanProgress(planId) {
    // Background execution is checked for up to 2 minutes.
    for (let attempt = 0; attempt < 60; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const plan = await fetchPlan(planId);
      updatePlanMessage(plan);

      if (
        !["queued", "running"].includes(plan.status)
      ) {
        return plan;
      }
    }

    return fetchPlan(planId);
  }

  async function handlePlanAction(planId, action) {
    if (busyPlanId) return;

    setBusyPlanId(planId);

    try {
      const response = await fetch(
        `${API_URL}/orchestrator/plans/${planId}/${action}`,
        { method: "POST" }
      );

      const plan = await readResponse(response);
      updatePlanMessage(plan);

      if (action === "execute" && ["queued", "running"].includes(plan.status)) {
        try {
          await pollPlanProgress(planId);
        } catch (pollError) {
          console.error("Progress polling failed:", pollError);
          // Keep the latest accepted plan visible. User can refresh manually.
        }
      }
    } catch (error) {
      console.error(error);
      alert(`Could not ${action} plan: ${error.message}`);
    } finally {
      setBusyPlanId(null);
    }
  }

  async function sendOrchestratorRequest(text, conversationId) {
    const response = await fetch(`${API_URL}/orchestrator/plans`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        request: text,
        conversation_id: conversationId,
      }),
    });

    const plan = await readResponse(response);

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        type: "plan",
        plan,
      },
    ]);
  }

  async function sendChatMessage(text, conversationId) {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: text,
      }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Chat request failed");
    }

    if (!response.body) {
      throw new Error("No response body");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let assistantText = "";

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "" },
    ]);

    while (true) {
      const { value, done } = await reader.read();

      if (done) break;

      assistantText += decoder.decode(value, {
        stream: true,
      });

      setMessages((prev) => {
        const updated = [...prev];
        const lastAssistantIndex = updated.length - 1;

        updated[lastAssistantIndex] = {
          role: "assistant",
          content: assistantText,
        };

        return updated;
      });
    }

    assistantText += decoder.decode();

    if (assistantText) {
      setMessages((prev) => {
        const updated = [...prev];

        updated[updated.length - 1] = {
          role: "assistant",
          content: assistantText,
        };

        return updated;
      });
    }
  }

  async function sendMessage() {
    const text = input.trim();

    if (!text || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: text },
    ]);

    setInput("");
    setLoading(true);

    try {
      let conversationId = currentId;

      if (!conversationId) {
        conversationId = await createConversation(
        text.length > 40 ? `${text.substring(0, 40)}...` : text,
        false
        );
      }

      if (isOrchestratorRequest(text)) {
        await sendOrchestratorRequest(text, conversationId);
      } else {
        await sendChatMessage(text, conversationId);
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Sorry, something went wrong: ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chat-page">
      <aside className="chat-history">
        <div className="chat-history-heading">
          <span>CONVERSATIONS</span>

          <button
            className="icon-button"
            onClick={() => createConversation()}
            title="New conversation"
          >
            <Plus size={17} />
          </button>
        </div>

        <button
          className="new-chat-button"
          onClick={() => createConversation()}
        >
          <Plus size={16} />
          New conversation
        </button>

        <div className="conversation-list">
          {conversations.length === 0 && (
            <div className="conversation-empty">
              No conversations yet
            </div>
          )}

          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`conversation-item ${
                currentId === conversation.id ? "active" : ""
              }`}
            >
              <button
                className="conversation-select"
                onClick={() => selectConversation(conversation.id)}
              >
                <MessageSquare size={15} />
                <span>
                  {conversation.title || "New conversation"}
                </span>
              </button>

              <button
                className="conversation-delete"
                onClick={() => deleteConversation(conversation.id)}
                title="Delete conversation"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      <section className="chat-main">
        <div className="chat-main-header">
          <div>
            <h2>AI Assistant</h2>
            <span>
              <span className="status-dot" />
              Qwen3:8B · RAG + ATO
            </span>
          </div>

          <div className="chat-mode-label">
            <Sparkles size={14} />
            Local AI
          </div>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <div className="welcome-icon">
                <Sparkles size={25} />
              </div>

              <h1>How can I help you?</h1>

              <p>
                Ask questions about your documents, chat with your
                local AI assistant, or ask ATO to create tasks and reminders.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`message-row ${message.role}`}
            >
              <div className="message-avatar">
                {message.role === "user" ? "U" : "AI"}
              </div>

              <div className="message-body">
                <div className="message-role">
                  {message.role === "user" ? "You" : "Assistant"}
                </div>

                {message.type === "plan" ? (
                  <PlanCard
                    plan={message.plan}
                    busy={busyPlanId === message.plan?.id}
                    onAction={handlePlanAction}
                    onRefresh={refreshPlan}
                  />
                ) : (
                  <div className="message-content">
                    {message.content}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="chat-loading">
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span className="loading-dot" />
              <span>AI is thinking...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <div className="chat-input-box">
            <DocumentUpload />

            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message your AI assistant..."
              rows={1}
              disabled={loading}
            />

            <button
              className="send-button"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              title="Send message"
            >
              <Send size={17} />
            </button>
          </div>

          <div className="chat-input-hint">
            Enter to send · Shift + Enter for new line
          </div>
        </div>
      </section>
    </div>
  );
}

export default ChatPage;
