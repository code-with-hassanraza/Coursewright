import { useState, useRef, useEffect } from 'react'
import { sendMessage } from '../../services/chatService'

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-md px-md py-sm text-left ${
          isUser
            ? 'bg-primary text-on-primary font-body-sm text-body-sm'
            : 'bg-surface-card border border-hairline-soft font-body-sm text-body-sm text-ink'
        }`}
      >
        {msg.content}
      </div>
    </div>
  )
}

export default function Chatbot({ specializationId, roadmapId, isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your learning assistant. Ask me anything about this roadmap or specialization.",
    },
  ])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [isOpen])

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || isSending) return

    setInput('')
    setError(null)
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setIsSending(true)

    try {
      const { reply } = await sendMessage({ message: text, specializationId, roadmapId })
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }])
    } catch {
      setError('Failed to get a response. Please try again.')
      setMessages((prev) => prev.slice(0, -1))
      setInput(text)
    } finally {
      setIsSending(false)
    }
  }

  if (!isOpen) return null

  return (
    <>
      <div className="fixed inset-0 z-20 bg-ink/20 md:hidden" onClick={onClose} />
      <div className="fixed bottom-0 right-0 top-16 z-30 flex w-full flex-col border-l border-hairline-soft bg-canvas shadow-xl md:w-96">
        <div className="flex items-center justify-between border-b border-hairline-soft px-lg py-md">
          <div className="flex items-center gap-xs">
            <span className="material-symbols-outlined text-primary">smart_toy</span>
            <p className="font-body-strong text-body-strong text-ink">Learning Assistant</p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-surface-card"
            aria-label="Close chat"
          >
            <span className="material-symbols-outlined text-mute">close</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-lg py-md">
          <div className="flex flex-col gap-md">
            {messages.map((msg, i) => (
              <Message key={i} msg={msg} />
            ))}
            {isSending && (
              <div className="flex justify-start">
                <div className="rounded-md border border-hairline-soft bg-surface-card px-md py-sm">
                  <span className="flex gap-xs">
                    <span className="h-2 w-2 animate-bounce rounded-full bg-ash [animation-delay:0ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-ash [animation-delay:150ms]" />
                    <span className="h-2 w-2 animate-bounce rounded-full bg-ash [animation-delay:300ms]" />
                  </span>
                </div>
              </div>
            )}
            {error && (
              <p className="text-center font-body-sm text-body-sm text-error">{error}</p>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <form onSubmit={handleSend} className="border-t border-hairline-soft p-lg">
          <div className="flex gap-xs">
            <input
              ref={inputRef}
              type="text"
              className="input flex-1"
              placeholder="Ask something…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isSending}
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              className="btn-primary shrink-0 px-md"
              aria-label="Send"
            >
              <span className="material-symbols-outlined">send</span>
            </button>
          </div>
        </form>
      </div>
    </>
  )
}