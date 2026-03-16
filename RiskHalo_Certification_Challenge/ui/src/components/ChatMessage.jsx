import React from 'react'

export default function ChatMessage({ role, content }) {
  const isUser = role === 'user'

  const renderContent = () => {
    if (isUser || !content) return content

    const headingStarts = [
      '1. Summary Insight',
      'Summary Insight',
      '2. Supporting Evidence from Sessions',
      'Supporting Evidence from Sessions',
      '3. Behavioral Interpretation',
      'Behavioral Interpretation',
      '4. Performance Recommendation',
      'Performance Recommendation',
    ]

    return String(content)
      .split('\n')
      .map((line, idx) => {
        const trimmed = line.trim()
        const isHeading = headingStarts.some((h) => trimmed.startsWith(h))

        if (isHeading) {
          return (
            <div key={idx} className="chat-heading-line">
              <span className="chat-heading">{line}</span>
            </div>
          )
        }

        return (
          <div key={idx}>
            {line}
          </div>
        )
      })
  }

  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : 'chat-message-assistant'}`}>
      <div className="chat-message-bubble">
        {renderContent()}
      </div>
    </div>
  )
}
