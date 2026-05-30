// WebSocket message types — must match api.py protocol

export type AgentName = "evaluator" | "router" | "researcher" | "architect" | "coder" | "reviewer" | "verifier";
export type AgentStatus = "idle" | "running" | "done" | "reviewing";
export type ComplexityLevel = "simple" | "moderate" | "complex" | "critical";

export interface AgentStatusMsg  { type: "agent_status";    agent: AgentName; status: AgentStatus; }
export interface ChatMsg          { type: "chat_message";    agent: AgentName; model: string; content: string; ts: string; }
export interface CostUpdateMsg    { type: "cost_update";     agent: AgentName; tokens: number; cost_usd: number; }
export interface UpgradePromptMsg { type: "upgrade_prompt";  recommended_model: string; benchmark_reason: string; score: string; cost_per_1m: string; }
export interface BrowserUpdateMsg { type: "browser_update";  url: string; scanning: boolean; }
export interface TestResultMsg    { type: "test_result";     name: string; passed: boolean; duration_ms: number; }
export interface WorkflowDoneMsg  { type: "workflow_complete"; summary: Record<string, unknown>; }
export interface ErrorMsg         { type: "error";           message: string; }

export type WSMessage =
  | AgentStatusMsg | ChatMsg | CostUpdateMsg | UpgradePromptMsg
  | BrowserUpdateMsg | TestResultMsg | WorkflowDoneMsg | ErrorMsg;

export interface AgentState {
  name: AgentName;
  emoji: string;
  displayName: string;
  model: string;
  status: AgentStatus;
}

export interface ChatMessage {
  id: string;
  agent: AgentName | "user" | "system";
  from: string;
  model: string;
  content: string;
  ts: string;
}

export interface TestResult {
  name: string;
  passed: boolean;
  duration_ms: number;
}

export interface WorkflowUIState {
  status: "idle" | "running" | "complete" | "error";
  taskText: string;
  taskType: string;
  agents: Record<AgentName, AgentState>;
  messages: ChatMessage[];
  totalTokens: number;
  totalCost: number;
  elapsedMs: number;
  browserUrl: string;
  browserScanning: boolean;
  testResults: TestResult[];
  upgradePrompt: UpgradePromptMsg | null;
  progress: number;
}
