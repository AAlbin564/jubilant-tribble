import { useEffect, useRef } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Message } from "../types";

export function MessageList({ messages }: { messages: Message[] }) {
    const listRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const list = listRef.current
        if (list) list.scrollTop = list.scrollHeight
    }, [messages])

    return (
        <div className="message-list" ref={listRef}>
            {messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                    {message.role === "assistant" ? (
                        <Markdown
                            remarkPlugins={[remarkGfm]}
                            components={{ a: (props) => <a {...props} target="_blank" rel="noreferrer" /> }}
                        >
                            {message.text_content}
                        </Markdown>
                    ) : (
                        message.text_content
                    )}
                </div>
            ))}
        </div>
    );
}
