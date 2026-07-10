import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Provider, useDispatch, useSelector } from "react-redux";
import { configureStore, createAsyncThunk, createSlice, nanoid } from "@reduxjs/toolkit";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import clsx from "clsx";
import {
  Activity,
  Bot,
  CalendarCheck,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  Frown,
  LockKeyhole,
  Moon,
  SendHorizontal,
  Smile,
  Sparkles,
  SunMedium,
  TimerReset,
  UserRound,
  Wrench
} from "lucide-react";

import "./style.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const api = axios.create({ baseURL: API_BASE_URL, headers: { "Content-Type": "application/json" } });

async function streamChat({ sessionId, message, interactionId }, handlers) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, interaction_id: interactionId, stream: true })
  });
  if (!response.ok || !response.body) throw new Error(`Chat request failed with ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      const lines = block.split("\n");
      const eventLine = lines.find((line) => line.startsWith("event:"));
      const dataLine = lines.find((line) => line.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      handlers[eventLine.replace("event:", "").trim()]?.(JSON.parse(dataLine.replace("data:", "").trim()));
    }
  }
}

const fetchDashboard = createAsyncThunk("dashboard/fetch", async () => {
  const { data } = await api.get("/dashboard");
  return data;
});

const interactionSlice = createSlice({
  name: "interaction",
  initialState: { current: null },
  reducers: {
    setInteraction(state, action) {
      state.current = action.payload;
    }
  }
});

const dashboardSlice = createSlice({
  name: "dashboard",
  initialState: {
    data: {
      today_interactions: 0,
      pending_follow_ups: 0,
      positive_sentiment: 0,
      negative_sentiment: 0,
      recent_interactions: [],
      pending_reminders: [],
      tool_history: []
    },
    status: "idle",
    error: null
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboard.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.status = "ready";
        state.data = action.payload;
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message;
      });
  }
});

const chatSlice = createSlice({
  name: "chat",
  initialState: {
    sessionId: `session-${nanoid()}`,
    messages: [
      {
        id: "welcome",
        role: "assistant",
        content: "I am ready to manage the HCP interaction form. Tell me what happened in the meeting, what to update, or what follow-up you need.",
        createdAt: new Date().toISOString()
      }
    ],
    currentTool: null,
    currentModel: "gemma2-9b-it",
    status: "ready",
    error: null,
    toolLog: [],
    toast: null
  },
  reducers: {
    addUserMessage: {
      reducer(state, action) {
        state.messages.push(action.payload);
      },
      prepare(content) {
        return { payload: { id: nanoid(), role: "user", content, createdAt: new Date().toISOString() } };
      }
    },
    startAssistantMessage(state) {
      state.status = "thinking";
      state.error = null;
      state.messages.push({ id: nanoid(), role: "assistant", content: "", streaming: true, createdAt: new Date().toISOString() });
    },
    appendAssistantToken(state, action) {
      const message = state.messages[state.messages.length - 1];
      if (message?.role === "assistant") message.content += action.payload;
    },
    finishAssistantMessage(state, action) {
      const message = state.messages[state.messages.length - 1];
      if (message?.role === "assistant") {
        message.content = action.payload.message || message.content;
        message.streaming = false;
      }
      state.status = "ready";
      state.currentTool = action.payload.current_tool ?? state.currentTool;
      state.currentModel = action.payload.metadata?.model ?? state.currentModel;
      state.toast = "CRM updated by AI assistant";
      if (state.toolLog[0]) state.toolLog[0].status = "success";
    },
    setTool(state, action) {
      state.currentTool = action.payload.name;
      state.toolLog.unshift({
        id: nanoid(),
        tool_name: action.payload.name,
        input_json: JSON.stringify(action.payload.arguments ?? {}),
        status: "running",
        created_at: new Date().toISOString()
      });
    },
    setChatError(state, action) {
      state.status = "error";
      state.error = action.payload;
      state.toast = action.payload;
      if (state.toolLog[0]) state.toolLog[0].status = "error";
      const message = state.messages[state.messages.length - 1];
      if (message?.streaming) {
        message.streaming = false;
        message.content = action.payload;
      }
    },
    clearToast(state) {
      state.toast = null;
    }
  }
});

const { setInteraction } = interactionSlice.actions;
const { addUserMessage, appendAssistantToken, clearToast, finishAssistantMessage, setChatError, setTool, startAssistantMessage } =
  chatSlice.actions;

const store = configureStore({
  reducer: {
    chat: chatSlice.reducer,
    dashboard: dashboardSlice.reducer,
    interaction: interactionSlice.reducer
  }
});

function App() {
  const dispatch = useDispatch();
  const [darkMode, setDarkMode] = useState(false);
  const chat = useSelector((state) => state.chat);
  const interaction = useSelector((state) => state.interaction.current);
  const dashboard = useSelector((state) => state.dashboard.data);

  useEffect(() => {
    dispatch(fetchDashboard());
  }, [dispatch]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  async function handleSend(message) {
    dispatch(addUserMessage(message));
    dispatch(startAssistantMessage());
    try {
      await streamChat(
        { sessionId: chat.sessionId, message, interactionId: interaction?.id },
        {
          tool: (payload) => dispatch(setTool(payload)),
          token: (payload) => dispatch(appendAssistantToken(payload.content)),
          done: (payload) => {
            dispatch(finishAssistantMessage(payload));
            if (payload.interaction) dispatch(setInteraction(payload.interaction));
            dispatch(fetchDashboard());
          },
          error: (payload) => dispatch(setChatError(payload.message))
        }
      );
    } catch (error) {
      dispatch(setChatError(error.message));
    }
  }

  return (
    <main className="min-h-screen bg-cloud text-slate-950 transition-colors dark:bg-slate-950 dark:text-slate-100">
      <TopNav aiStatus={chat.status} currentTool={chat.currentTool} model={chat.currentModel} darkMode={darkMode} onToggleDark={() => setDarkMode((value) => !value)} />
      <div className="mx-auto grid max-w-[1600px] gap-4 px-4 py-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(420px,0.9fr)]">
        <section className="space-y-4">
          <DashboardCards dashboard={dashboard} />
          <InteractionForm interaction={interaction} />
          <div className="grid gap-4 xl:grid-cols-2">
            <ToolHistory localTools={chat.toolLog} persistedTools={dashboard.tool_history} />
            <RecentActivity interactions={dashboard.recent_interactions} reminders={dashboard.pending_reminders} />
          </div>
        </section>
        <ChatPanel messages={chat.messages} status={chat.status} onSend={handleSend} />
      </div>
      <Toast message={chat.toast} onClose={() => dispatch(clearToast())} />
    </main>
  );
}

function TopNav({ aiStatus, currentTool, model, darkMode, onToggleDark }) {
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded bg-brand text-white">
            <Sparkles size={21} />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-normal text-slate-950 dark:text-white">AI-First HCP CRM</h1>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Healthcare interaction management</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge icon={Activity} tone={aiStatus === "ready" ? "green" : "amber"} label={aiStatus === "ready" ? "AI Ready" : "AI Thinking"} />
          <Badge icon={DatabaseZap} tone="blue" label={`Tool: ${currentTool ?? "idle"}`} />
          <Badge icon={Bot} tone="slate" label={`Model: ${model}`} />
          <button type="button" title="Toggle dark mode" onClick={onToggleDark} className="inline-flex h-10 w-10 items-center justify-center rounded border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:border-brand hover:text-brand dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
            {darkMode ? <SunMedium size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </div>
    </header>
  );
}

function Badge({ icon: Icon, label, tone = "slate" }) {
  const tones = {
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/20",
    amber: "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/20",
    blue: "bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-500/10 dark:text-blue-300 dark:ring-blue-500/20",
    slate: "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700"
  };
  return (
    <span className={clsx("inline-flex min-h-9 items-center gap-2 rounded px-3 py-1.5 text-xs font-semibold ring-1", tones[tone])}>
      {Icon ? <Icon size={15} /> : null}
      <span className="max-w-[220px] truncate">{label}</span>
    </span>
  );
}

function DashboardCards({ dashboard }) {
  const cards = [
    ["Today's Interactions", "today_interactions", CalendarCheck, "text-brand"],
    ["Pending Follow Ups", "pending_follow_ups", TimerReset, "text-amber"],
    ["Positive Sentiment", "positive_sentiment", Smile, "text-mint"],
    ["Negative Sentiment", "negative_sentiment", Frown, "text-coral"]
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(([label, key, Icon, color]) => (
        <article key={key} className="rounded border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-normal text-slate-500 dark:text-slate-400">{label}</p>
              <p className="mt-2 text-3xl font-extrabold">{dashboard?.[key] ?? 0}</p>
            </div>
            <Icon className={color} size={24} />
          </div>
        </article>
      ))}
    </div>
  );
}

function InteractionForm({ interaction }) {
  const fields = [
    ["HCP Name", (i) => i?.hcp?.name],
    ["Hospital", (i) => i?.hcp?.hospital],
    ["Specialization", (i) => i?.hcp?.specialization],
    ["Interaction Type", (i) => i?.interaction_type],
    ["Date", (i) => i?.interaction_date],
    ["Time", (i) => i?.interaction_time],
    ["Attendees", (i) => i?.attendees],
    ["Topics Discussed", (i) => i?.topics_discussed],
    ["Voice Summary", (i) => i?.voice_summary],
    ["Materials Shared", (i) => i?.materials_shared],
    ["Samples Distributed", (i) => i?.samples_distributed],
    ["Sentiment", (i) => i?.sentiment],
    ["Outcome", (i) => i?.outcome],
    ["Follow Up", (i) => i?.follow_up],
    ["Notes", (i) => i?.notes]
  ];
  return (
    <section className="rounded border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-slate-950 dark:text-white">Interaction Details</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">Read-only form controlled by LangGraph tools</p>
        </div>
        <span className="inline-flex items-center gap-2 rounded bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
          <LockKeyhole size={14} />
          AI controlled
        </span>
      </div>
      <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">
        {fields.map(([label, selector]) => {
          const value = selector(interaction);
          const longField = ["Topics Discussed", "Voice Summary", "Outcome", "Follow Up", "Notes"].includes(label);
          return (
            <label key={label} className={longField ? "md:col-span-2 xl:col-span-3" : ""}>
              <span className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400">{label}</span>
              <div className="min-h-11 rounded border border-slate-200 bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-800 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100">
                {value ? String(value) : <span className="text-slate-400">Awaiting AI update</span>}
              </div>
            </label>
          );
        })}
      </div>
    </section>
  );
}

function ToolHistory({ localTools = [], persistedTools = [] }) {
  const rows = [...localTools, ...persistedTools].slice(0, 8);
  return (
    <section className="rounded border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex items-center gap-2">
        <Wrench size={18} className="text-brand" />
        <h2 className="text-sm font-bold">Tool Execution History</h2>
      </div>
      <div className="space-y-2">
        {rows.length === 0 ? <p className="text-sm text-slate-500">No tools have run yet.</p> : null}
        {rows.map((row, index) => (
          <div key={`${row.id}-${index}`} className="rounded border border-slate-200 p-3 text-xs dark:border-slate-800">
            <div className="flex items-center justify-between gap-3">
              <span className="font-bold text-slate-900 dark:text-white">{row.tool_name}</span>
              <span className="rounded bg-slate-100 px-2 py-1 font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{row.status}</span>
            </div>
            <p className="mt-2 line-clamp-2 text-slate-500 dark:text-slate-400">{row.input_json}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function RecentActivity({ interactions = [], reminders = [] }) {
  return (
    <section className="rounded border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-3 flex items-center gap-2">
        <Clock3 size={18} className="text-mint" />
        <h2 className="text-sm font-bold">Recent Activity</h2>
      </div>
      <div className="space-y-3">
        {interactions.slice(0, 4).map((interaction) => (
          <div key={interaction.id} className="border-b border-slate-100 pb-3 text-sm last:border-0 dark:border-slate-800">
            <p className="font-semibold">{interaction.hcp?.name}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {interaction.interaction_date ?? "No date"} | {interaction.sentiment}
            </p>
          </div>
        ))}
        {reminders.slice(0, 3).map((reminder) => (
          <div key={`reminder-${reminder.id}`} className="rounded bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-500/10 dark:text-amber-200">
            <p className="font-semibold">{reminder.title}</p>
            <p className="text-xs">{new Date(reminder.due_at).toLocaleString()}</p>
          </div>
        ))}
        {interactions.length === 0 && reminders.length === 0 ? <p className="text-sm text-slate-500">Activity will appear after the assistant runs tools.</p> : null}
      </div>
    </section>
  );
}

function ChatPanel({ messages, status, onSend }) {
  const [text, setText] = useState("");
  const listRef = useRef(null);
  const busy = status === "thinking";
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);
  function submit(event) {
    event.preventDefault();
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    onSend(message);
  }
  return (
    <aside className="flex h-[calc(100vh-96px)] min-h-[660px] flex-col rounded border border-slate-200 bg-white shadow-soft dark:border-slate-800 dark:bg-slate-900 lg:sticky lg:top-20">
      <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <h2 className="text-sm font-bold">AI Assistant</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">ChatGPT-style CRM control with streaming responses</p>
      </div>
      <div ref={listRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {busy ? <TypingAnimation /> : null}
      </div>
      <form onSubmit={submit} className="border-t border-slate-200 p-3 dark:border-slate-800">
        <div className="flex items-end gap-2 rounded border border-slate-200 bg-slate-50 p-2 focus-within:border-brand dark:border-slate-700 dark:bg-slate-950">
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) submit(event);
            }}
            rows={2}
            placeholder="Tell the assistant what happened with the HCP..."
            className="min-h-12 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-slate-400"
          />
          <button type="submit" disabled={busy || !text.trim()} title="Send message" className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded bg-brand text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300 dark:disabled:bg-slate-700">
            <SendHorizontal size={18} />
          </button>
        </div>
      </form>
    </aside>
  );
}

function MessageBubble({ message }) {
  const assistant = message.role === "assistant";
  const Icon = assistant ? Bot : UserRound;
  return (
    <div className={`flex gap-3 ${assistant ? "" : "flex-row-reverse"}`}>
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded ${assistant ? "bg-brand text-white" : "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-100"}`}>
        <Icon size={17} />
      </div>
      <div className={`max-w-[88%] rounded px-3 py-2 text-sm leading-6 ${assistant ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-slate-100" : "bg-brand text-white"}`}>
        {assistant ? <ReactMarkdown>{message.content || " "}</ReactMarkdown> : message.content}
      </div>
    </div>
  );
}

function TypingAnimation() {
  return (
    <div className="ml-11 flex items-center gap-1 text-xs font-semibold text-slate-500">
      <span className="h-2 w-2 animate-bounce rounded-full bg-brand [animation-delay:-0.2s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-brand [animation-delay:-0.1s]" />
      <span className="h-2 w-2 animate-bounce rounded-full bg-brand" />
      <span className="ml-2">AI thinking</span>
    </div>
  );
}

function Toast({ message, onClose }) {
  useEffect(() => {
    if (!message) return undefined;
    const timer = window.setTimeout(onClose, 3200);
    return () => window.clearTimeout(timer);
  }, [message, onClose]);
  if (!message) return null;
  return (
    <div className="fixed bottom-4 left-1/2 z-40 flex -translate-x-1/2 items-center gap-2 rounded bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-soft dark:bg-white dark:text-slate-950">
      <CheckCircle2 size={18} className="text-emerald-400" />
      {message}
    </div>
  );
}

const router = createBrowserRouter([{ path: "/", element: <App /> }]);

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>
  </React.StrictMode>
);
