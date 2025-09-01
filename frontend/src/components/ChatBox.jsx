import React, { useEffect, useRef, useState } from 'react'

function Avatar({ role }) {
  return (
    <div className={`avatar ${role === 'user' ? 'avatar--user' : 'avatar--assistant'}`}>
      {role === 'user' ? '🧑' : '🤖'}
    </div>
  )
}

function Typing() {
  return (
    <span className="typing-inline">
      <span></span><span></span><span></span>
    </span>
  )
}

function MessageBubble({ content, role, onCopy, showTyping = false }) {
  const [showCopy, setShowCopy] = useState(false)
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      onCopy && onCopy()
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  return (
    <div 
      className={`bubble ${role === 'user' ? 'bubble--user' : 'bubble--assistant'}`}
      onMouseEnter={() => setShowCopy(true)}
      onMouseLeave={() => setShowCopy(false)}
    >
      <div className="bubble-content">
        {content}
        {showTyping && <Typing />}
      </div>
      {showCopy && (
        <button 
          className="copy-button"
          onClick={handleCopy}
          title="Copy message"
        >
          📋
        </button>
      )}
    </div>
  )
}

export default function ChatBox({ messages, typing }) {
  const endRef = useRef(null)
  const [copyFeedback, setCopyFeedback] = useState('')
  
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  const handleCopy = () => {
    setCopyFeedback('Copied!')
    setTimeout(() => setCopyFeedback(''), 2000)
  }

  return (
    <div className="chatbox">
      {copyFeedback && (
        <div className="copy-feedback">{copyFeedback}</div>
      )}
      
      {messages.map((m, index) => {
        const isLastAssistantMessage = typing && 
          m.role === 'assistant' && 
          index === messages.length - 1
        
        return (
          <div key={m.id} className={`message ${m.role === 'user' ? 'message--user' : 'message--assistant'}`}>
            <Avatar role={m.role} />
            <MessageBubble 
              content={m.content} 
              role={m.role} 
              onCopy={handleCopy}
              showTyping={isLastAssistantMessage}
            />
          </div>
        )
      })}

      <div ref={endRef} />
    </div>
  )
}
