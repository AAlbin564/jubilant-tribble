import { useEffect, useRef } from "react";
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
                    {message.text_content}
                </div>
            ))}
        </div>
    );
}
