import { useState, useRef, useCallback, useEffect } from 'react'
import type { WSMessage, WorkflowUIState, AgentName, AgentState, ChatMessage, TestResult } from '../types'

const AGENT_META: Record<AgentName, { emoji: string; displayName: string; defaultModel: string }> = {
  evaluator: { emoji: '🎯', displayName: 'Evaluator',  defaultModel: 'qwen2.5-coder:7b' },
  router:    { emoji: '⚡', displayName: 'Router',     defaultModel: 'qwen2.5-coder:7b' },
  researcher:{ emoji: '🔭', displayName: 'Researcher', defaultModel: 'qwen2.5-coder:7b' },
  architect: { emoji: '🏛',  displayName: 'Architect',  defaultModel: 'qwen2.5-coder:7b' },
  coder:     { emoji: '⌨️', displayName: 'Coder',      defaultModel: 'qwen2.5-coder:7b' },
  reviewer:  { emoji: '🔍', displayName: 'Reviewer',   defaultModel: 'qwen2.5-coder:7b' },
  verifier:  { emoji: '🧪', displayName: 'Verifier',   defaultModel: 'qwen2.5-coder:7b + docker' },
}

const AGENT_ORDER: AgentName[] = ['evaluator','router','researcher','architect','coder','reviewer','verifier']

function makeInitialState(): WorkflowUIState {
  const agents = {} as Record<AgentName, AgentState>
  for (const [name, meta] of Object.entries(AGENT_META)) {
    agents[name as AgentName] = { name: name as AgentName, ...meta, model: meta.defaultModel, status: 'idle' }
  }
  return {
    status: 'idle', taskText: '', taskType: 'PENDING',
    agents, messages: [], totalTokens: 0, totalCost: 0, elapsedMs: 0,
    browserUrl: '', browserScanning: false, testResults: [],
    upgradePrompt: null, progress: 0,
  }
}

export function useWorkflow(wsUrl = 'ws://localhost:8000/ws') {
  const [state, setState] = useState<WorkflowUIState>(makeInitialState)
  const wsRef = useRef<WebSocket | null>(null)
  const startRef = useRef<number>(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const sendMsg = useCallback((msg: object) => {
    wsRef.current?.send(JSON.stringify(msg))
  }, [])

  const submitTask = useCallback((task: string) => {
    if (wsRef.current) wsRef.current.close()

    setState(() => ({ ...makeInitialState(), status: 'running', taskText: task }))
    startRef.current = Date.now()
    timerRef.current = setInterval(() => {
      setState(s => ({ ...s, elapsedMs: Date.now() - startRef.current }))
    }, 100)

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => ws.send(JSON.stringify({ type: 'task', task }))

    ws.onmessage = (e) => {
      const msg: WSMessage = JSON.parse(e.data)
      setState(prev => applyMessage(prev, msg))
    }

    ws.onclose = () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [wsUrl])

  const respondToUpgrade = useCallback((accepted: boolean) => {
    sendMsg({ type: 'upgrade_response', accepted })
    setState(s => ({ ...s, upgradePrompt: null }))
  }, [sendMsg])

  const sendInterrupt = useCallback((text: string) => {
    sendMsg({ type: 'interrupt', text })
  }, [sendMsg])

  useEffect(() => () => {
    wsRef.current?.close()
    if (timerRef.current) clearInterval(timerRef.current)
  }, [])

  return { state, submitTask, respondToUpgrade, sendInterrupt }
}

function applyMessage(prev: WorkflowUIState, msg: WSMessage): WorkflowUIState {
  switch (msg.type) {
    case 'agent_status': {
      const agents = { ...prev.agents }
      agents[msg.agent] = { ...agents[msg.agent], status: msg.status }
      const doneCount = AGENT_ORDER.filter(a => agents[a].status === 'done').length
      return { ...prev, agents, progress: Math.round((doneCount / AGENT_ORDER.length) * 100) }
    }
    case 'chat_message': {
      const newMsg: ChatMessage = {
        id: `${msg.agent}-${Date.now()}`,
        agent: msg.agent, from: AGENT_META[msg.agent].displayName,
        model: msg.model, content: msg.content, ts: msg.ts,
      }
      const agents = { ...prev.agents }
      agents[msg.agent] = { ...agents[msg.agent], model: msg.model }
      return { ...prev, agents, messages: [...prev.messages, newMsg] }
    }
    case 'cost_update':
      return { ...prev, totalTokens: prev.totalTokens + msg.tokens, totalCost: prev.totalCost + msg.cost_usd }
    case 'upgrade_prompt':
      return { ...prev, upgradePrompt: msg }
    case 'browser_update':
      return { ...prev, browserUrl: msg.url, browserScanning: msg.scanning }
    case 'test_result': {
      const tr: TestResult = { name: msg.name, passed: msg.passed, duration_ms: msg.duration_ms }
      return { ...prev, testResults: [...prev.testResults, tr] }
    }
    case 'workflow_complete':
      return { ...prev, status: 'complete', progress: 100 }
    case 'error':
      return { ...prev, status: 'error' }
    default:
      return prev
  }
}
