import { useWorkflow } from './hooks/useWorkflow'
import { TopBar } from './components/TopBar'
import { AgentPanel } from './components/AgentPanel'
import { ChatArea } from './components/ChatArea'
import { DetailsPanel } from './components/DetailsPanel'

export default function App() {
  const { state, submitTask, respondToUpgrade, sendInterrupt } = useWorkflow()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopBar state={state} />

      {/* Progress strip */}
      <div style={{ height: 3, background: 'var(--border)', flexShrink: 0, overflow: 'hidden' }}>
        <div style={{ height: '100%', background: 'linear-gradient(90deg, var(--amber-dim), var(--amber))', width: `${state.progress}%`, transition: 'width 0.8s ease' }} />
      </div>

      {/* Three-column layout */}
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr 320px', flex: 1, overflow: 'hidden', minHeight: 0 }}>
        <AgentPanel state={state} />
        <ChatArea state={state} onSubmitTask={submitTask} onInterrupt={sendInterrupt} />
        <DetailsPanel state={state} onUpgradeResponse={respondToUpgrade} />
      </div>
    </div>
  )
}
