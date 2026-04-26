// SSE consumer for the chat agent — keep in sync with finbot/apps/appwsrv/agent/runner.py.

import type { RichBlock } from "./types";

export type ChatEvent =
  | { type: "assistant_message_start" }
  | { type: "text_delta"; delta: string }
  | {
      type: "tool_call_start";
      id: string;
      name: string;
      label: string;
      icon: string;
    }
  | {
      type: "tool_call_end";
      id: string;
      status: "done" | "error";
      result_summary?: string;
    }
  | { type: "rich_block"; block: RichBlock }
  | { type: "error"; message: string }
  | { type: "done" };

export interface ChatHistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export class ChatUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ChatUnavailableError";
  }
}

export async function* streamChat(
  endpoint: string,
  accessToken: string,
  messages: ChatHistoryMessage[],
  signal?: AbortSignal,
): AsyncGenerator<ChatEvent> {
  const response = await fetch(`${endpoint}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ messages }),
    signal,
  });

  if (response.status === 503) {
    throw new ChatUnavailableError(
      "Chat assistant is not configured on this server.",
    );
  }
  if (!response.ok || !response.body) {
    throw new Error(`chat request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let sep: number;
    while ((sep = buf.indexOf("\n\n")) !== -1) {
      const frame = buf.slice(0, sep);
      buf = buf.slice(sep + 2);

      let eventName: string | null = null;
      let dataLine = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) eventName = line.slice(6).trim();
        else if (line.startsWith("data:"))
          dataLine += line.slice(5).trimStart();
      }
      if (!eventName) continue;
      const payload = dataLine ? JSON.parse(dataLine) : {};
      yield { type: eventName, ...payload } as ChatEvent;
    }
  }
}
