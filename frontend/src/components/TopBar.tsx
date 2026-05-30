import type { WorkflowUIState } from '../types'

interface Props { state: WorkflowUIState }

export function TopBar({ state }: Props) {
  const elapsed = (state.elapsedMs / 1000).toFixed(1) + 's'
  return (
    <header style={{
      height: 52, background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', padding: '0 20px', gap: 24, flexShrink: 0,
    }}>
      <div style={{ fontFamily: 'var(--display)', fontWeight: 800, fontSize: 18, color: 'var(--text-hi)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 28, height: 28, background: 'var(--amber)',
          clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
          animation: 'pulse-icon 3s ease-in-out infinite', flexShrink: 0,
        }} />
        ForgeLab
      </div>
      <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-dim)', borderLeft: '1px solid var(--border)', paddingLeft: 24 }}>
        one model · seven minds · zero api cost by default
      </div>
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 16 }}>
        {state.status === 'running' && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--teal)' }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--teal)', animation: 'blink 1.4s infinite' }} />
            {elapsed}
          </div>
        )}
        <div style={{
          fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--amber)',
          background: 'var(--amber-glow)', border: '1px solid var(--amber-dim)',
          borderRadius: 4, padding: '3px 10px',
        }}>
          ${state.totalCost.toFixed(2)}
        </div>
      </div>
    </header>
  )
}
