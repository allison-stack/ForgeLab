import type { WorkflowUIState, AgentName } from '../types'

const AGENT_ORDER: AgentName[] = ['evaluator','router','researcher','architect','coder','reviewer','verifier']

const STATUS_COLORS: Record<string, string> = {
  idle: 'var(--border-hi)', running: 'var(--amber)', done: 'var(--teal)', reviewing: 'var(--purple)',
}

interface Props { state: WorkflowUIState }

export function AgentPanel({ state }: Props) {
  return (
    <div style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ padding: '14px 16px 10px', fontFamily: 'var(--mono)', fontSize: 10, letterSpacing: '0.12em', color: 'var(--text-dim)', textTransform: 'uppercase', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        Agent Pipeline
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {AGENT_ORDER.map((name, i) => {
          const agent = state.agents[name]
          const isActive = agent.status === 'running' || agent.status === 'reviewing'
          return (
            <div key={name}>
              <div style={{
                display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 16px',
                background: isActive ? 'var(--elevated)' : 'transparent',
                position: 'relative',
              }}>
                {isActive && <div style={{ position: 'absolute', left: 0, top: 8, bottom: 8, width: 2, background: 'var(--amber)', borderRadius: '0 2px 2px 0' }} />}
                <div style={{
                  width: 32, height: 32, borderRadius: 6, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, flexShrink: 0, border: `1px solid ${STATUS_COLORS[agent.status]}`,
                  background: agent.status === 'running' ? 'var(--amber-glow)' : agent.status === 'done' ? '#00C9A711' : agent.status === 'reviewing' ? '#9B7FFF11' : 'var(--bg)',
                  opacity: agent.status === 'idle' ? 0.4 : 1,
                  animation: agent.status === 'running' ? 'spin-glow 2s linear infinite' : 'none',
                }}>
                  {agent.emoji}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: 'var(--display)', fontWeight: 600, fontSize: 12, color: 'var(--text-hi)' }}>{agent.displayName}</div>
                  <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: agent.status === 'running' ? 'var(--amber)' : agent.status === 'done' ? 'var(--teal)' : 'var(--text-dim)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {agent.model}
                  </div>
                </div>
                <div style={{ width: 6, height: 6, borderRadius: '50%', marginTop: 4, background: STATUS_COLORS[agent.status], flexShrink: 0, animation: agent.status === 'running' ? 'blink 1s infinite' : 'none' }} />
              </div>
              {i < AGENT_ORDER.length - 1 && (
                <div style={{ marginLeft: 39, height: 12, borderLeft: `1px dashed ${agent.status === 'done' ? 'var(--amber-dim)' : 'var(--border)'}` }} />
              )}
            </div>
          )
        })}
      </div>
      <div style={{ borderTop: '1px solid var(--border)', padding: '12px 16px', flexShrink: 0 }}>
        {[
          ['TOKENS',  String(state.totalTokens.toLocaleString()), 'amber'],
          ['ELAPSED', (state.elapsedMs / 1000).toFixed(1) + 's', ''],
          ['MODEL',   state.agents.coder.model, 'teal'],
        ].map(([label, value, color]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)', letterSpacing: '0.06em' }}>{label}</span>
            <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: color === 'amber' ? 'var(--amber)' : color === 'teal' ? 'var(--teal)' : 'var(--text-hi)' }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
