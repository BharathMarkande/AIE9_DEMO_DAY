import React, { useState, useRef, useEffect } from 'react'

const SUGGESTED_QUESTIONS = [
  'Am I escalating risk after losses?',
  'What does my post-loss performance indicate?',
  'Am I cutting profits too early?',
  'Am I improving over time?',
  'Is my execution becoming more stable?',
]

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const [displayedText, setDisplayedText] = useState('')
  const [questionIndex, setQuestionIndex] = useState(0)
  const [isTyping, setIsTyping] = useState(true)
  const [showOverlay, setShowOverlay] = useState(true)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!showOverlay || disabled) return

    const question = SUGGESTED_QUESTIONS[questionIndex]
    const isComplete = displayedText.length >= question.length

    if (isTyping) {
      if (isComplete) {
        const pauseTimer = setTimeout(() => {
          setIsTyping(false)
        }, 2000)
        return () => clearTimeout(pauseTimer)
      }
      const typeTimer = setTimeout(() => {
        setDisplayedText(question.slice(0, displayedText.length + 1))
      }, 60)
      return () => clearTimeout(typeTimer)
    } else {
      if (displayedText.length === 0) {
        setQuestionIndex((prev) => (prev + 1) % SUGGESTED_QUESTIONS.length)
        setIsTyping(true)
        return
      }
      const deleteTimer = setTimeout(() => {
        setDisplayedText(displayedText.slice(0, -1))
      }, 30)
      return () => clearTimeout(deleteTimer)
    }
  }, [displayedText, questionIndex, isTyping, showOverlay, disabled])

  const handleFocus = () => setShowOverlay(false)
  const handleBlur = () => setShowOverlay(value.trim() === '')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    setShowOverlay(true)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleOverlayClick = () => {
    textareaRef.current?.focus()
  }

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="chat-input-wrapper">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={disabled}
          aria-label="Message"
        />
        {showOverlay && (
          <div
            className="chat-input-typing-overlay"
            onClick={handleOverlayClick}
            aria-hidden
          >
            <span className="chat-input-typing-text">{displayedText}</span>
            <span className="chat-input-typing-cursor">|</span>
          </div>
        )}
      </div>
      <button type="submit" className="btn-send" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  )
}
