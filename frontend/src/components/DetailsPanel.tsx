import { useState } from 'react'
import type { WorkflowUIState } from '../types'

interface Props { state: WorkflowUIState; onUpgradeResponse: (accepted: boolean) => void }

export function DetailsPanel({ state, onUpgradeResponse }: Props) {
  const [activeTab, setActiveTab] = useState<'browser' | 'models' | 'verify'>('browser')

  const TABS = ['browser', 'models', 'verify'] as const

  return (
    <div style={{ background: 'var(--surface)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        {TABS.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            flex: 1, padding: '10px 0', textAlign: 'center', fontFamily: 'var(--mono)', fontSize: 10, letterSpacing: '0.06em',
            color: activeTab === tab ? 'var(--amber)' : 'var(--text-dim)', cursor: 'pointer', border: 'none',
            borderBottom: `2px solid ${activeTab === tab ? 'var(--amber)' : 'transparent'}`,
            background: 'none', textTransform: 'uppercase' as const,
          }}>
            {tab}
          </button>
        ))}
      </div>

      {/* Browser Tab */}
      {activeTab === 'browser' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ background: 'var(--elevated)', borderBottom: '1px solid var(--border)', padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 5 }}>
              {['#FF5F57','#FFBD2E','#28CA42'].map(c => <span key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />)}
            </div>
            <div style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 4, padding: '4px 10px', fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {state.browserUrl || 'about:blank'}
            </div>
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12, background: 'var(--elevated)', position: 'relative', overflow: 'hidden' }}>
            {state.browserScanning && (
              <div style={{ position: 'absolute', left: 0, right: 0, height: 2, background: 'linear-gradient(90deg, transparent, var(--amber), transparent)', animation: 'scan 2s linear infinite' }} />
            )}
            {state.browserUrl ? (
              <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--teal)', textAlign: 'center' }}>
                🌐 Researcher browsing<br /><span style={{ color: 'var(--text-dim)', fontSize: 9 }}>{state.browserUrl}</span>
              </div>
            ) : (
              <>
                <div style={{ fontSize: 28, opacity: 0.2 }}>🌐</div>
                <div style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-dim)', textAlign: 'center', lineHeight: 1.7 }}>
                  Browser idle<br /><span style={{ fontSize: 9 }}>Researcher activates Playwright<br />when web search is needed</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
          {Object.values(state.agents).map(agent => (
            <div key={agent.name} style={{ background: 'var(--elevated)', border: `1px solid ${agent.status === 'running' ? 'var(--amber)' : 'var(--border)'}`, borderRadius: 6, padding: '10px 12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                <span style={{ fontSize: 13 }}>{agent.emoji}</span>
                <span style={{ fontFamily: 'var(--display)', fontWeight: 600, fontSize: 11, color: 'var(--text-hi)' }}>{agent.displayName}</span>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 9, padding: '1px 6px', borderRadius: 2, marginLeft: 'auto', background: agent.status === 'running' ? 'var(--amber-glow)' : '#3DDB8511', color: agent.status === 'running' ? 'var(--amber)' : 'var(--green)', border: `1px solid ${agent.status === 'running' ? 'var(--amber-dim)' : '#3DDB8533'}`, animation: agent.status === 'running' ? 'blink 1.2s infinite' : 'none' }}>
                  {agent.status === 'running' ? 'ACTIVE' : 'READY'}
                </span>
              </div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--teal)' }}>{agent.model}</div>
            </div>
          ))}
          {state.upgradePrompt && (
            <div style={{ background: 'var(--elevated)', border: '1px solid var(--amber)', borderRadius: 6, padding: '12px' }}>
              <div style={{ fontFamily: 'var(--display)', fontWeight: 700, fontSize: 12, color: 'var(--amber)', marginBottom: 6 }}>⬆ Upgrade Recommended</div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text)', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--teal)' }}>{state.upgradePrompt.recommended_model}</strong><br />
                {state.upgradePrompt.benchmark_reason}<br />
                Score: {state.upgradePrompt.score} · {state.upgradePrompt.cost_per_1m}/1M tokens
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button onClick={() => onUpgradeResponse(true)} style={{ flex: 1, background: 'var(--amber)', color: '#000', border: 'none', borderRadius: 4, padding: '6px', fontFamily: 'var(--display)', fontWeight: 700, fontSize: 11, cursor: 'pointer' }}>Accept</button>
                <button onClick={() => onUpgradeResponse(false)} style={{ flex: 1, background: 'var(--elevated)', color: 'var(--text)', border: '1px solid var(--border-hi)', borderRadius: 4, padding: '6px', fontFamily: 'var(--mono)', fontSize: 11, cursor: 'pointer' }}>Stay Local</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Verify Tab */}
      {activeTab === 'verify' && (
        <div style={{ flex: 1, overflowY: 'auto', padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'var(--elevated)', border: '1px solid var(--border-hi)', borderRadius: 6, padding: '10px 12px' }}>
            <span style={{ fontSize: 18 }}>🐳</span>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text)', lineHeight: 1.5 }}>
              <span style={{ color: 'var(--teal)' }}>testforge-sandbox</span> container<br />deterministic execution · no hallucination
            </div>
          </div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10, letterSpacing: '0.1em', color: 'var(--text-dim)', textTransform: 'uppercase' as const }}>Test Results</div>
          {state.testResults.length === 0 ? (
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text-dim)', textAlign: 'center', padding: '20px 0' }}>Verifier not yet active</div>
          ) : (
            state.testResults.map(tr => (
              <div key={tr.name} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', background: 'var(--elevated)', borderRadius: 4, border: `1px solid ${tr.passed ? '#3DDB8533' : '#FF5C5C33'}`, fontFamily: 'var(--mono)', fontSize: 10, animation: 'fadeUp 0.3s ease both' }}>
                <span style={{ fontSize: 11 }}>{tr.passed ? '✅' : '❌'}</span>
                <span style={{ flex: 1, color: 'var(--text)' }}>{tr.name}</span>
                <span style={{ color: 'var(--text-dim)' }}>{tr.duration_ms}ms</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
