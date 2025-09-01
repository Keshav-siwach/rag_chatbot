import React, { useEffect, useMemo, useRef, useState } from 'react'
import ChatBox from './components/ChatBox'
import ChatInput from './components/ChatInput'

const WS_URL = 'ws://localhost:8000/chat'

export default function App() {
  const wsRef = useRef(null)
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState([
    { id: 'sys-1', role: 'assistant', content: 'Hi! Ask me about your documents.' },
  ])
  const streamRef = useRef({ id: null })
  const [isTyping, setIsTyping] = useState(false)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)
    ws.onclose = () => { setConnected(false); setIsTyping(false); streamRef.current.id = null }
    ws.onerror = () => { setConnected(false); setIsTyping(false); streamRef.current.id = null }

    ws.onmessage = (event) => {
      const token = event.data
      if (token === '__END__') {
        streamRef.current.id = null
        setIsTyping(false)
        return
      }
      if (token === '__ERROR__') {
        streamRef.current.id = null
        setIsTyping(false)
        setMessages((prev) => ([...prev, { id: crypto.randomUUID(), role: 'assistant', content: 'An error occurred.' }]))
        return
      }
      // Ensure a single assistant bubble is used during streaming
      setMessages((prev) => {
        const currentId = streamRef.current.id
        if (currentId && prev[prev.length - 1]?.id === currentId) {
          const copy = prev.slice()
          copy[copy.length - 1] = {
            ...copy[copy.length - 1],
            content: copy[copy.length - 1].content + token,
          }
          return copy
        }
        const id = currentId || crypto.randomUUID()
        if (!currentId) streamRef.current.id = id
        return [...prev, { id, role: 'assistant', content: token.trim() }]
      })
    }

    return () => {
      ws.close()
    }
  }, [])

  const sendQuestion = (text) => {
    if (!text?.trim()) return
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: text }])
    setIsTyping(true)
    streamRef.current.id = null
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ question: text }))
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="brand">
          <div className="brand__logo">AI</div>
          <div className="brand__name">RAG Chatbot</div>
        </div>
        <span className={connected ? 'status status--ok' : 'status status--down'}>
          <span className="dot"></span>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </header>
      <main className="app__main">
        <ChatBox messages={messages} typing={isTyping} />
      </main>
      <footer className="app__footer">
        <ChatInput onSend={sendQuestion} disabled={!connected} />
      </footer>
    </div>
  )
}
