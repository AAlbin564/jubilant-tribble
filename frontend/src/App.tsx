import './App.css'
import { ChatFormField } from './components/ChatFormField';
import { useState } from 'react';

import {sendMessage} from './api';

import { MessageList } from './components/MessageList';
import type { Message } from './types';
function App() {
  const [threadId] = useState(() => crypto.randomUUID());



  const [messages, setMessages] = useState<Message[]>([]);

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (text: string) => {
  setMessages((prev) => [...prev, { role: "user", text_content: text }]);
  setLoading(true);
  try {
    const reply = await sendMessage(threadId, text);
    setMessages((prev) => [...prev, { role: "assistant", text_content: reply }]);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "Unknown error";
    setMessages((prev) => [...prev, { role: "assistant", text_content: `Sorry, something went wrong: ${detail}` }]);
  } finally {
    setLoading(false);
  }
};
  

  return (
    <>
    <div className="title">
      <h1>Mushroom Assistant</h1>
    </div>
    <div className="chat-box">
      <MessageList messages={messages}/>
      <ChatFormField onSend={handleSubmit} loading={loading}/>
    </div>
    </>
    
  )
}

export default App
