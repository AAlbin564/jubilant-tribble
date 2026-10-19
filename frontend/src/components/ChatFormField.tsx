import { useState } from "react";
import type { SubmitEvent } from "react";

export function ChatFormField({ onSend, loading }: { onSend: (text: string) => void; loading: boolean }) {
    const [text, setText] = useState("")

    const addToMessageList = (e: SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();
        const trimmed = text.trim();
        if (!trimmed || loading) return;
        onSend(trimmed);
        setText("");
    }

    return(
        <div className="chat-container"> 
        
        <form onSubmit={addToMessageList}>
            <input 
            maxLength={2000}
            value={text}
            placeholder="Ask mushroom related questions here"
            onChange={(e) => setText(e.target.value)}
            />
            <button type="submit" disabled={loading}>
                {loading ? "Sending..." : "Send"}
            </button>
        </form>
        
        </div>
    )
}