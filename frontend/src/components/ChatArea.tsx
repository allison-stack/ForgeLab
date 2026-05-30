import { useEffect, useRef, useState } from 'react'
import type { WorkflowUIState, AgentName } from '../types'

const AGENT_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  evaluator:  { bg: 'var(--amber-glow)',  border: 'var(--amber-dim)',    text: 'var(--amber)' },
  router:     { bg: 'var(--amber-glow)',  border: 'var(--amber-dim)',    text: 'var(--amber)' },
  researcher: { bg: '#00C9A711',          border: '#00C9A744',           text: 'var(--teal)' },
  architect:  { bg: '#60A5FA11',          border: '#60A5FA44',           text: '#60A5FA' },
  coder:      { bg: '#60A5FA11',          border: '#60A5FA44',           text: '#60A5FA' },
  reviewer:   { bg: '#9B7FFF11',          border: '#9B7FFF44',           text: 'var(--purple)' },
  verifier:   { bg: '#3DDB8511',          border: '#3DDB8544',           text: 'var(--green)' },
  user:       { bg: '#7C3AED22',          border: '#7C3AED44',           text: '#A78BFA' },
  system:     { bg: 'var(--elevated)',    border: 'var(--border)',       text: 'var(--text-dim)' },
}

const EMOJIS: Record<string, string> = {
  evaluator:'🎯', router:'⚡', researcher:'🔭', architect:'🏛', coder:'⌨️', reviewer:'🔍', verifier:'🧪', user:'👤', system:'📋'
}

interface Props {
  state: WorkflowUIState
  onSubmitTask: (task: string) => void
  onInterrupt: (text: string) => void
}

export function ChatArea({ state, onSubmitTask, onInterrupt }: Props) {
  const messagesRef = useRef<HTMLDivElement>(null)
  const [input, setInput] = useState('')
  const isRunning = state.status === 'running'

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight
    }
  }, [state.messages])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter' || !input.trim()) return
    const text = input.trim()
    setInput('')
    if (!isRunning) {
      onSubmitTask(text)
    } else {
      onInterrupt(text)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg)' }}>
      {/* Task bar */}
      <div style={{ background: 'var(--elevated)', borderBottom: '1px solid var(--border)', padding: '10px 20px', display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 8px', borderRadius: 3, background: 'var(--amber-glow)', color: 'var(--amber)', border: '1px solid var(--amber-dim)', letterSpacing: '0.06em', textTransform: 'uppercase' as const, flexShrink: 0 }}>
          {state.taskType || 'PENDING'}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-hi)', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {state.taskText || 'Waiting for task...'}
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesRef} style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 0 }}>
        {state.messages.map((msg) => {
          const colors = AGENT_COLORS[msg.agent] || AGENT_COLORS.system
          return (
            <div key={msg.id} style={{ display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)', animation: 'fadeUp 0.35s cubic-bezier(0.22,1,0.36,1) both' }}>
              <div style={{ width: 28, height: 28, borderRadius: 5, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0, marginTop: 2, background: colors.bg, border: `1px solid ${colors.border}` }}>
                {EMOJIS[msg.agent] || '?'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontFamily: 'var(--display)', fontWeight: 600, fontSize: 11, color: colors.text }}>{msg.from}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--text-dim)' }}>{msg.model}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 9, color: 'var(--text-dim)', marginLeft: 'auto' }}>{msg.ts}</span>
                </div>
                <div style={{ fontSize: 12.5, lineHeight: 1.65, color: 'var(--text)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {msg.content}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Input bar */}
      <div style={{ background: 'var(--elevated)', border: '1px solid var(--border-hi)', borderBottom: 'none', borderRadius: '8px 8px 0 0', padding: '10px 16px', margin: '0 20px', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
        <span style={{ fontSize: 14 }}>⚡</span>
        <input
          style={{ flex: 1, background: 'none', border: 'none', outline: 'none', fontFamily: 'var(--sans)', fontSize: 13, color: 'var(--text-hi)' }}
          placeholder={isRunning ? 'Interrupt agents — redirect, add requirements...' : 'Describe a task for the ForgeLab team...'}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)', padding: '6px 20px 12px', flexShrink: 0 }}>
        Press <kbd style={{ fontFamily: 'var(--mono)', fontSize: 9, background: 'var(--elevated)', border: '1px solid var(--border-hi)', borderRadius: 3, padding: '1px 5px', color: 'var(--text)' }}>Enter</kbd> to {isRunning ? 'interrupt' : 'submit'} · agents adapt dynamically
      </div>
    </div>
  )
}
