import type { ChatRequest, ChatResponse } from "./types";

export async function sendMessage(threadId: string, text: string): Promise<string> {
  const body: ChatRequest = { thread_id: threadId, text_content: text };

  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => null);
    const detail = typeof error?.detail === "string" ? error.detail : `Request failed (${res.status})`;
    throw new Error(detail);
  }

  const data: ChatResponse = await res.json();
  return data.text_content;
}