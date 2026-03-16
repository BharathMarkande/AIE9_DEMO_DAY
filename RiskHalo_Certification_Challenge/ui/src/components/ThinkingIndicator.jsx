import React from 'react'

export default function ThinkingIndicator() {
  return (
    <div className="chat-message chat-message-assistant">
      <div className="chat-message-bubble thinking-bubble">
        <span className="thinking-label">🤖 Thinking</span>
        <span className="thinking-dots">
          <span className="dot">.</span>
          <span className="dot">.</span>
          <span className="dot">.</span>
        </span>
        <p className="thinking-sub">📊 Analyzing behavioral patterns...</p>
      </div>
    </div>
  )
}
