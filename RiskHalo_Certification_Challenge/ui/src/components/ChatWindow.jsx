import React, { useState, useRef, useEffect } from 'react'
import { askQuestion } from '../services/api'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import ThinkingIndicator from './ThinkingIndicator'

export default function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)
  const streamedRef = useRef('')

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, streamingContent])

  const handleSend = async (text) => {
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setIsStreaming(true)
    setStreamingContent('')
    streamedRef.current = ''

    try {
      await askQuestion(text, (chunk) => {
        streamedRef.current += chunk
        setStreamingContent(streamedRef.current)
      })
    } catch (err) {
      setError(err.message || 'Failed to get response')
    } finally {
      const fullContent = streamedRef.current
      if (fullContent) {
        setMessages((prev) => [...prev, { role: 'assistant', content: fullContent }])
      }
      setStreamingContent('')
      streamedRef.current = ''
      setIsStreaming(false)
    }
  }

  return (
    <section className="glass-card chat-panel">
      <h2 className="panel-title">RiskHalo AI Coach</h2>
      <div className="chat-window" ref={scrollRef}>
        {messages.length === 0 && !isStreaming && (
          <p className="chat-placeholder">
            Ask about your sessions, behavioral patterns, or risk discipline.
          </p>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} role={m.role} content={m.content} />
        ))}
        {isStreaming && !streamingContent && <ThinkingIndicator />}
        {isStreaming && streamingContent && (
          <div className="chat-message chat-message-assistant">
            <div className="chat-message-bubble streaming-bubble">
              {streamingContent}
            </div>
          </div>
        )}
        {error && (
          <p className="chat-error">{error}</p>
        )}
      </div>
      <div className="chat-input-wrap">
        <ChatInput onSend={handleSend} disabled={isStreaming} />
      </div>
    </section>
  )
}
