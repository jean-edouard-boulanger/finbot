import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Sparkles,
  Send,
  User,
  Loader2,
  Square,
  Wallet,
  TrendingUp,
  CreditCard,
  PiggyBank,
  Calendar,
  RefreshCw,
} from "lucide-react";

import AuthContext from "contexts/auth/auth-context";
import { APP_SERVICE_ENDPOINT } from "utils/env-config";
import { cn } from "lib/utils";
import { Button } from "components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetDescription,
} from "components/ui/sheet";

import type { RichBlock } from "./types";
import { ChartBlockView } from "./chart-block";
import { iconFromName } from "./icon-map";
import { ChatUnavailableError, streamChat } from "./stream";

// ---------- Types ----------

type Role = "user" | "assistant";

interface ToolCall {
  id: string;
  label: string;
  iconName: string;
  status: "running" | "done" | "error";
  resultSummary?: string;
}

interface Message {
  id: string;
  role: Role;
  content: string;
  toolCalls?: ToolCall[];
  richBlocks?: RichBlock[];
  isStreaming?: boolean;
  failed?: boolean;
}

// ---------- Rich-block renderer ----------

interface RichBlockViewProps {
  block: RichBlock;
  interactive?: boolean;
  onClarificationPick?: (sendText: string) => void;
}

function ClarificationBlockView({
  block,
  interactive,
  onPick,
}: {
  block: Extract<RichBlock, { kind: "clarification" }>;
  interactive: boolean;
  onPick?: (sendText: string) => void;
}) {
  return (
    <div className="mt-3 rounded-lg border border-border/60 bg-card/50 px-3 py-2.5">
      <div className="text-sm font-medium text-foreground/90">
        {block.title}
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {block.options.map((opt, i) => (
          <Button
            key={i}
            size="sm"
            variant="outline"
            disabled={!interactive}
            onClick={() => onPick?.(opt.send_text)}
            className="h-7 rounded-full text-xs font-normal"
          >
            {opt.label}
          </Button>
        ))}
      </div>
    </div>
  );
}

function RichBlockView({
  block,
  interactive,
  onClarificationPick,
}: RichBlockViewProps) {
  if (block.kind === "kv") {
    return (
      <div className="mt-3 overflow-hidden rounded-lg border border-border/60 bg-card/50">
        <div className="border-b border-border/60 bg-muted/30 px-3 py-1.5 text-xs font-medium text-muted-foreground">
          {block.title}
        </div>
        <div className="divide-y divide-border/50">
          {block.rows.map((row, i) => (
            <div
              key={i}
              className="flex items-center justify-between px-3 py-2 text-sm"
            >
              <span className="text-muted-foreground">{row.label}</span>
              <span
                className={cn(
                  "font-medium tabular-nums",
                  row.tone === "up" && "text-emerald-600 dark:text-emerald-400",
                  row.tone === "down" && "text-rose-600 dark:text-rose-400",
                )}
              >
                {row.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  if (block.kind === "table") {
    return (
      <div className="mt-3 overflow-hidden rounded-lg border border-border/60 bg-card/50">
        <div className="border-b border-border/60 bg-muted/30 px-3 py-1.5 text-xs font-medium text-muted-foreground">
          {block.title}
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/40 text-xs text-muted-foreground">
              {block.headers.map((h, i) => (
                <th
                  key={i}
                  className={cn(
                    "px-3 py-1.5 text-left font-normal",
                    i > 0 && "text-right",
                  )}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, i) => (
              <tr key={i} className="border-b border-border/30 last:border-b-0">
                {row.map((cell, j) => (
                  <td
                    key={j}
                    className={cn(
                      "px-3 py-1.5",
                      j > 0 && "text-right tabular-nums",
                      j === 0 && "text-foreground",
                      j > 0 && "text-foreground/90",
                    )}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {block.footer && (
          <div className="border-t border-border/40 bg-muted/20 px-3 py-1.5 text-xs italic text-muted-foreground">
            {block.footer}
          </div>
        )}
      </div>
    );
  }
  if (block.kind === "chart") {
    return <ChartBlockView block={block} />;
  }
  if (block.kind === "clarification") {
    return (
      <ClarificationBlockView
        block={block}
        interactive={!!interactive}
        onPick={onClarificationPick}
      />
    );
  }
  // callout
  const toneClasses =
    block.tone === "success"
      ? "border-emerald-500/30 bg-emerald-500/10"
      : "border-amber-500/30 bg-amber-500/10";
  return (
    <div
      className={cn("mt-3 rounded-lg border px-3 py-2 text-sm", toneClasses)}
    >
      <div className="font-medium">{block.title}</div>
      <div className="mt-0.5 text-foreground/80">{block.body}</div>
    </div>
  );
}

// ---------- Lightweight markdown (bold only) ----------

function renderInlineMarkdown(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

// ---------- Tool call pill ----------

function ToolCallsView({ calls }: { calls: ToolCall[] }) {
  const [expanded, setExpanded] = useState(false);
  if (calls.length === 0) return null;

  const showAll = expanded || calls.length === 1;
  const visible = showAll ? calls : [calls[calls.length - 1]];
  const hiddenCount = calls.length - visible.length;
  const allDone = calls.every((c) => c.status !== "running");

  return (
    <div className="space-y-1">
      {visible.map((c) => (
        <ToolCallPill key={c.id} call={c} />
      ))}
      {calls.length > 1 && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="ml-1 text-[11px] text-muted-foreground transition-colors hover:text-foreground"
        >
          {expanded
            ? "Hide earlier steps"
            : `+ ${hiddenCount} earlier step${hiddenCount === 1 ? "" : "s"}${
                allDone ? "" : " (in progress)"
              }`}
        </button>
      )}
    </div>
  );
}

function ToolCallPill({ call }: { call: ToolCall }) {
  const Icon = iconFromName(call.iconName);
  const isError = call.status === "error";
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border px-2.5 py-1.5 text-xs",
        isError
          ? "border-rose-500/30 bg-rose-500/10"
          : "border-border/60 bg-muted/40",
        call.status === "running" && "animate-pulse",
      )}
    >
      {call.status === "running" ? (
        <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin text-muted-foreground" />
      ) : (
        <Icon
          className={cn(
            "h-3.5 w-3.5 shrink-0",
            isError ? "text-rose-500" : "text-muted-foreground",
          )}
        />
      )}
      <span
        className={cn(
          isError ? "text-rose-600 dark:text-rose-400" : "text-foreground/80",
        )}
      >
        {call.label}
      </span>
      {call.status !== "running" && call.resultSummary && (
        <span className="ml-auto truncate text-muted-foreground">
          {call.resultSummary}
        </span>
      )}
    </div>
  );
}

// ---------- Message bubble ----------

interface MessageViewProps {
  message: Message;
  isLatestAssistant: boolean;
  onClarificationPick: (sendText: string) => void;
}

function MessageView({
  message,
  isLatestAssistant,
  onClarificationPick,
}: MessageViewProps) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end gap-2">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-3.5 py-2 text-sm text-primary-foreground">
          {message.content}
        </div>
        <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
          <User className="h-3.5 w-3.5" />
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-2">
      <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-linear-to-br from-violet-500 to-indigo-600 text-white shadow-xs">
        <Sparkles className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1 space-y-2">
        {message.toolCalls && message.toolCalls.length > 0 && (
          <ToolCallsView calls={message.toolCalls} />
        )}
        {message.content && (
          <div className="text-sm leading-relaxed text-foreground/90">
            {renderInlineMarkdown(message.content)}
            {message.isStreaming && (
              <span className="ml-0.5 inline-block h-3.5 w-1.5 translate-y-0.5 animate-pulse bg-foreground/60" />
            )}
          </div>
        )}
        {message.richBlocks?.map((block, i) => (
          <RichBlockView
            key={i}
            block={block}
            interactive={isLatestAssistant && !message.isStreaming}
            onClarificationPick={onClarificationPick}
          />
        ))}
      </div>
    </div>
  );
}

// ---------- Suggested prompts ----------

const SUGGESTIONS: { icon: React.FC<{ className?: string }>; text: string }[] =
  [
    { icon: Wallet, text: "What's my net worth right now?" },
    { icon: CreditCard, text: "How much did I spend last month?" },
    { icon: RefreshCw, text: "Review my active subscriptions" },
    { icon: PiggyBank, text: "Am I on track with my savings rate?" },
    { icon: TrendingUp, text: "Summarise my investment portfolio" },
    { icon: Calendar, text: "What were my biggest expenses recently?" },
  ];

function EmptyState({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-2 py-8">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-linear-to-br from-violet-500 to-indigo-600 text-white shadow-lg shadow-violet-500/20">
        <Sparkles className="h-6 w-6" />
      </div>
      <h3 className="mt-4 text-base font-semibold">Ask Finbot anything</h3>
      <p className="mt-1 max-w-sm text-center text-sm text-muted-foreground">
        I have access to your accounts, transactions and holdings. Ask me a
        question or pick a suggestion below.
      </p>
      <div className="mt-6 grid w-full grid-cols-1 gap-2 sm:grid-cols-2">
        {SUGGESTIONS.map((s, i) => {
          const Icon = s.icon;
          return (
            <button
              key={i}
              onClick={() => onPick(s.text)}
              className="group flex items-start gap-2 rounded-lg border border-border/60 bg-card/30 px-3 py-2.5 text-left text-sm transition-all hover:-translate-y-px hover:border-border hover:bg-accent/40 hover:shadow-xs"
            >
              <Icon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground" />
              <span className="text-foreground/80 group-hover:text-foreground">
                {s.text}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------- Main drawer ----------

interface ChatDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({
  open,
  onOpenChange,
}) => {
  const { accessToken } = useContext(AuthContext);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const status = useMemo(() => (busy ? "Thinking…" : "Ready"), [busy]);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-grow textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  // Focus on open
  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [open]);

  const updateMessage = useCallback(
    (id: string, updater: (m: Message) => Message) => {
      setMessages((prev) => prev.map((m) => (m.id === id ? updater(m) : m)));
    },
    [],
  );

  const sendQuestion = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || busy) return;
      if (!accessToken) return;

      const userMsgId = `u-${Date.now()}`;
      const assistantMsgId = `a-${Date.now() + 1}`;

      // Snapshot prior history (text only — server is stateless and re-plans tool calls).
      const history = messages
        .filter((m) => m.content)
        .map((m) => ({ role: m.role, content: m.content }));
      history.push({ role: "user", content: trimmed });

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: trimmed },
        {
          id: assistantMsgId,
          role: "assistant",
          content: "",
          toolCalls: [],
          richBlocks: [],
          isStreaming: true,
        },
      ]);
      setInput("");
      setBusy(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        for await (const ev of streamChat(
          APP_SERVICE_ENDPOINT,
          accessToken,
          history,
          controller.signal,
        )) {
          switch (ev.type) {
            case "assistant_message_start":
              break;
            case "text_delta":
              updateMessage(assistantMsgId, (m) => ({
                ...m,
                content: m.content + ev.delta,
              }));
              break;
            case "tool_call_start":
              updateMessage(assistantMsgId, (m) => ({
                ...m,
                toolCalls: [
                  ...(m.toolCalls ?? []),
                  {
                    id: ev.id,
                    label: ev.label,
                    iconName: ev.icon,
                    status: "running",
                  },
                ],
              }));
              break;
            case "tool_call_end":
              updateMessage(assistantMsgId, (m) => ({
                ...m,
                toolCalls: m.toolCalls?.map((c) =>
                  c.id === ev.id
                    ? {
                        ...c,
                        status: ev.status,
                        resultSummary: ev.result_summary,
                      }
                    : c,
                ),
              }));
              break;
            case "rich_block":
              updateMessage(assistantMsgId, (m) => ({
                ...m,
                richBlocks: [...(m.richBlocks ?? []), ev.block],
              }));
              break;
            case "error":
              updateMessage(assistantMsgId, (m) => ({
                ...m,
                richBlocks: [
                  ...(m.richBlocks ?? []),
                  {
                    kind: "callout",
                    tone: "warning",
                    title: "Something went wrong",
                    body: ev.message,
                  },
                ],
                failed: true,
              }));
              break;
            case "done":
              break;
          }
        }
      } catch (err) {
        if (controller.signal.aborted) {
          updateMessage(assistantMsgId, (m) => ({
            ...m,
            content: m.content || "_Stopped._",
          }));
        } else if (err instanceof ChatUnavailableError) {
          updateMessage(assistantMsgId, (m) => ({
            ...m,
            richBlocks: [
              ...(m.richBlocks ?? []),
              {
                kind: "callout",
                tone: "warning",
                title: "Chat unavailable",
                body: err.message,
              },
            ],
            failed: true,
          }));
        } else {
          updateMessage(assistantMsgId, (m) => ({
            ...m,
            richBlocks: [
              ...(m.richBlocks ?? []),
              {
                kind: "callout",
                tone: "warning",
                title: "Network error",
                body:
                  err instanceof Error
                    ? err.message
                    : "Unable to reach the chat service.",
              },
            ],
            failed: true,
          }));
        }
      } finally {
        updateMessage(assistantMsgId, (m) => ({ ...m, isStreaming: false }));
        setBusy(false);
        abortRef.current = null;
      }
    },
    [accessToken, busy, messages, updateMessage],
  );

  const handleStop = () => {
    abortRef.current?.abort();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuestion(input);
    }
  };

  const handleReset = () => {
    if (busy) return;
    setMessages([]);
    setInput("");
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="flex w-full flex-col gap-0 p-0 sm:max-w-md md:max-w-lg lg:max-w-xl"
      >
        {/* Header — note: SheetContent renders its own absolute close X at top-4 right-4 */}
        <div className="flex shrink-0 items-center gap-3 border-b border-border/50 py-3 pl-4 pr-12">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-linear-to-br from-violet-500 to-indigo-600 text-white shadow-xs">
            <Sparkles className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <SheetTitle className="text-sm font-semibold leading-tight">
              Finbot Assistant
            </SheetTitle>
            <SheetDescription className="flex items-center gap-1.5 text-xs">
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  busy ? "bg-amber-500 animate-pulse" : "bg-emerald-500",
                )}
              />
              {status}
            </SheetDescription>
          </div>
          {messages.length > 0 && !busy && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 text-xs"
              onClick={handleReset}
            >
              New chat
            </Button>
          )}
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
          {messages.length === 0 ? (
            <EmptyState onPick={sendQuestion} />
          ) : (
            <div className="space-y-5">
              {(() => {
                let lastAssistantIdx = -1;
                for (let i = messages.length - 1; i >= 0; i--) {
                  if (messages[i].role === "assistant") {
                    lastAssistantIdx = i;
                    break;
                  }
                }
                return messages.map((m, i) => (
                  <MessageView
                    key={m.id}
                    message={m}
                    isLatestAssistant={i === lastAssistantIdx}
                    onClarificationPick={sendQuestion}
                  />
                ));
              })()}
            </div>
          )}
        </div>

        {/* Composer */}
        <div className="shrink-0 border-t border-border/50 bg-background/80 px-3 py-3 backdrop-blur-sm">
          <div
            className={cn(
              "flex items-end gap-2 rounded-xl border border-border bg-card px-2.5 py-2 transition-colors",
              "focus-within:border-foreground/30 focus-within:ring-2 focus-within:ring-violet-500/20",
            )}
          >
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your finances…"
              rows={1}
              disabled={busy}
              className="flex-1 resize-none bg-transparent px-1 py-1 text-sm leading-relaxed outline-hidden placeholder:text-muted-foreground disabled:opacity-60"
            />
            {busy ? (
              <Button
                size="icon"
                variant="outline"
                className="h-8 w-8 shrink-0 rounded-lg"
                onClick={handleStop}
                aria-label="Stop generating"
              >
                <Square className="h-3 w-3 fill-current" />
              </Button>
            ) : (
              <Button
                size="icon"
                className="h-8 w-8 shrink-0 rounded-lg bg-linear-to-br from-violet-500 to-indigo-600 hover:opacity-90"
                onClick={() => sendQuestion(input)}
                disabled={!input.trim() || !accessToken}
                aria-label="Send message"
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
          <p className="mt-1.5 px-1 text-[10px] text-muted-foreground">
            Finbot can make mistakes — check important information. Press{" "}
            <kbd className="rounded border border-border/60 bg-muted/50 px-1 font-mono text-[10px]">
              Enter
            </kbd>{" "}
            to send,{" "}
            <kbd className="rounded border border-border/60 bg-muted/50 px-1 font-mono text-[10px]">
              Shift+Enter
            </kbd>{" "}
            for newline.
          </p>
        </div>
      </SheetContent>
    </Sheet>
  );
};

// ---------- Floating launcher button ----------

interface ChatLauncherButtonProps {
  onClick: () => void;
}

export const ChatLauncherButton: React.FC<ChatLauncherButtonProps> = ({
  onClick,
}) => {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-full",
        "bg-linear-to-br from-violet-500 to-indigo-600 px-4 py-3 text-white",
        "shadow-lg shadow-violet-500/30 transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-violet-500/40",
        "focus:outline-hidden focus:ring-2 focus:ring-violet-500/40 focus:ring-offset-2 focus:ring-offset-background",
      )}
      aria-label="Open Finbot chat assistant"
    >
      <Sparkles className="h-4 w-4 transition-transform group-hover:rotate-12" />
      <span className="hidden text-sm font-medium sm:inline">Ask Finbot</span>
      <kbd className="hidden rounded border border-white/30 bg-white/10 px-1.5 py-0.5 font-mono text-[10px] sm:inline">
        ⌘K
      </kbd>
    </button>
  );
};
