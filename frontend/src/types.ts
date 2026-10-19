export type Message = {
    role: "user" | "assistant";
    text_content: string;
}

export type ChatRequest = {
  thread_id: string;
  text_content: string;
};

export type ChatResponse = {
  text_content: string;
};