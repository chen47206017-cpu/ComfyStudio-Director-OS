import { useCallback, useEffect, useMemo, useRef, useState, type DragEvent, type MouseEvent } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  useReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type NodeProps,
  type OnConnect,
  type Viewport,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import './styles.css'

type NodeKind =
  | 'asset'
  | 'character'
  | 'scene'
  | 'prop'
  | 'referenceImage'
  | 'referenceVideo'
  | 'audio'
  | 'shot'
  | 'prompt'
  | 'model'
  | 'output'

type Asset = {
  id: string
  name: string
  type: string
  description?: string
  tags?: string[]
}

type ReferenceRole = 'character_identity' | 'character_look' | 'scene' | 'prop' | 'previous_video' | 'continuity_frame' | 'motion_reference' | 'voice_identity' | 'exact_dialogue'

type ReferenceBinding = {
  id: string
  assetId: string
  assetName: string
  role: ReferenceRole
  sourceShot?: string
  enabled: boolean
}

type StudioNodeData = {
  label: string
  kind: NodeKind
  summary?: string
  assetId?: string
  assetType?: string
  state?: 'idle' | 'ready' | 'blocked' | 'running' | 'done'
  output?: string
  [key: string]: unknown
}

type StudioNode = Node<StudioNodeData>

type CanvasPayload = {
  nodes: StudioNode[]
  edges: Edge[]
  viewport?: Viewport
  revision?: number
  updatedAt?: string
  bindings?: ReferenceBinding[]
}

type DemoShot = {
  id: string
  title: string
  duration_seconds: number
  scene: string
  scene_text: string
  output: string
  previous_shot_id?: string | null
  status?: string
}

type DemoLane = 'local_comfy' | 'AutoDL5090' | 'API'

type DemoJobOutput = {
  id?: string | number
  verified?: boolean
  media_url?: string
  mime?: string
  filename?: string
  path?: string
  sha256?: string
  duration_seconds?: number
  duration?: number
}

type DemoRuntimeShot = {
  status?: string
  job_id?: string
  prompt_id?: string
  outputs?: DemoJobOutput[]
  reason_code?: string
}

type DemoFeedback = {
  tone: 'neutral' | 'working' | 'blocked' | 'failed' | 'success'
  title: string
  detail?: string
}

type DemoProjectPayload = {
  project: { id: string; title: string; description?: string; default_shot_id?: string }
  shots: DemoShot[]
  runtime?: { shots?: Record<string, DemoRuntimeShot> }
  assets?: Asset[]
  voices?: Array<Record<string, unknown>>
}

type HealthState = {
  studio: 'online' | 'offline' | 'checking'
  comfy: 'online' | 'offline' | 'unknown'
  label: string
}

type StudioMode = 'director' | 'engineering'

const API_CANDIDATES = {
  assets: ['/api/v10/assets', '/api/assets', '/director/assets'],
  canvas: ['/api/v10/canvas', '/api/v10/canvases/director', '/director/canvas'],
  canon: ['/api/v10/canon/check', '/api/v8/canon/check'],
  prompt: ['/api/v10/prompts/compile', '/api/v8/prompt/build'],
  health: ['/api/v10/health', '/api/v8/status', '/api/status'],
}

const NODE_LABELS: Record<NodeKind, string> = {
  asset: '资产',
  character: '角色',
  scene: '场景',
  prop: '道具',
  referenceImage: '图片参考',
  referenceVideo: '视频参考',
  audio: '音频',
  shot: '镜头',
  prompt: '提示词编译器',
  model: '模型路由',
  output: '生成结果',
}

const NODE_DESCRIPTIONS: Record<NodeKind, string> = {
  asset: '制作资产',
  character: 'Canon 锁定角色',
  scene: '年代与空间上下文',
  prop: '连续性道具',
  referenceImage: '图片参考槽位',
  referenceVideo: '动作视频参考',
  audio: '台词或环境声',
  shot: '镜头规格',
  prompt: '正向与反向提示词',
  model: 'ComfyUI 模型路由',
  output: '可验证生成结果',
}

const CANON_RULES: Record<NodeKind, NodeKind[]> = {
  asset: ['shot', 'referenceImage', 'referenceVideo', 'audio'],
  character: ['shot', 'prompt'],
  scene: ['shot', 'prompt'],
  prop: ['shot', 'prompt'],
  referenceImage: ['shot', 'prompt'],
  referenceVideo: ['shot', 'prompt'],
  audio: ['shot', 'prompt'],
  shot: ['prompt'],
  prompt: ['model'],
  model: ['output'],
  output: [],
}

const starterNodes: StudioNode[] = [
  {
    id: 'asset-studio',
    type: 'studio',
    position: { x: 60, y: 190 },
    data: { label: '2006设计工作室', kind: 'scene', assetId: 'SCENE_2006_STUDIO', state: 'ready' },
  },
  {
    id: 'shot-001',
    type: 'studio',
    position: { x: 330, y: 190 },
    data: { label: 'Shot 001 · 电话响起', kind: 'shot', summary: '中景 / 室内 / 2006', state: 'idle' },
  },
  {
    id: 'prompt-001',
    type: 'studio',
    position: { x: 620, y: 190 },
    data: { label: '提示词编译器', kind: 'prompt', summary: '等待 Canon 与资产', state: 'idle' },
  },
  {
    id: 'model-001',
    type: 'studio',
    position: { x: 920, y: 190 },
    data: { label: 'MiniMax H3 模型路由', kind: 'model', summary: 'ComfyUI · 8189', state: 'idle' },
  },
  {
    id: 'output-001',
    type: 'studio',
    position: { x: 1200, y: 190 },
    data: { label: '镜头 001 生成结果', kind: 'output', summary: '等待生成', state: 'idle' },
  },
]

const starterEdges: Edge[] = [
  { id: 'e-studio-shot', source: 'asset-studio', target: 'shot-001', type: 'smoothstep', animated: true },
  { id: 'e-shot-prompt', source: 'shot-001', target: 'prompt-001', type: 'smoothstep', animated: true },
  { id: 'e-prompt-model', source: 'prompt-001', target: 'model-001', type: 'smoothstep', animated: true },
  { id: 'e-model-output', source: 'model-001', target: 'output-001', type: 'smoothstep', animated: true },
]

const stateLabel: Record<NonNullable<StudioNodeData['state']>, string> = {
  idle: '待处理',
  ready: '已就绪',
  blocked: '已阻断',
  running: '运行中',
  done: '已完成',
}

const REFERENCE_ROLES: Array<{ id: ReferenceRole; label: string }> = [
  { id: 'character_identity', label: '角色身份' },
  { id: 'character_look', label: '角色造型' },
  { id: 'scene', label: '场景' },
  { id: 'prop', label: '道具' },
  { id: 'previous_video', label: '上一镜视频' },
  { id: 'continuity_frame', label: '连续性尾帧' },
  { id: 'motion_reference', label: '动作参考' },
  { id: 'voice_identity', label: '声音身份' },
  { id: 'exact_dialogue', label: '精确台词' },
]

const ASSET_TYPE_LABELS: Record<string, string> = {
  character: '角色',
  scene: '场景',
  prop: '道具',
  audio: '音频',
  image: '图片',
  video: '视频',
}

class ApiError extends Error {
  status: number
  payload: unknown

  constructor(status: number, statusText: string, payload: unknown) {
    const reason = summarizeApiPayload(payload, statusText || '请求失败')
    super(`HTTP ${status}${reason ? ` · ${reason}` : ''}`)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function summarizeApiPayload(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') return fallback
  const body = payload as Record<string, unknown>
  const parts: string[] = []
  for (const key of ['reason_code', 'error', 'message', 'status']) {
    if (typeof body[key] === 'string' && body[key]) parts.push(body[key] as string)
  }
  const nested = [body.canon_gate, body.preflight, body.prepared]
  for (const value of nested) {
    if (!value || typeof value !== 'object') continue
    const item = value as Record<string, unknown>
    if (typeof item.reason_code === 'string' && item.reason_code) parts.push(item.reason_code)
    for (const field of ['errors', 'issues']) {
      if (Array.isArray(item[field])) {
        parts.push(...item[field].slice(0, 2).map((entry) => {
          if (typeof entry === 'string') return entry
          if (entry && typeof entry === 'object' && typeof (entry as Record<string, unknown>).message === 'string') return String((entry as Record<string, unknown>).message)
          return String(entry)
        }))
      }
    }
  }
  return [...new Set(parts)].join('；') || fallback
}

function formatApiError(error: unknown, fallback: string): string {
  if (error instanceof ApiError) return `${fallback} · ${error.message}`
  if (error instanceof Error && error.message) return `${fallback} · ${error.message}`
  return fallback
}

function demoStatusLabel(status?: string): string {
  const labels: Record<string, string> = {
    READY: '已就绪', PREPARED: '已预检', QUEUED: '已排队', RUNNING: '运行中',
    COLLECTING: '回收中', SUCCEEDED: '已完成', FAILED: '失败', CANCELLED: '已取消', ORPHANED: '失联',
  }
  return labels[String(status ?? '').toUpperCase()] ?? (status || '待处理')
}

function demoStatusClass(status?: string): string {
  return String(status ?? 'pending').toLowerCase().replace(/[^a-z0-9_-]/g, '-')
}

const TERMINAL_DEMO_JOB_STATUSES = new Set(['SUCCEEDED', 'FAILED', 'CANCELLED', 'ORPHANED'])

function recordValue(value: unknown): Record<string, unknown> | null {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null
}

function stringValue(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value : undefined
}

function numberValue(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined
}

function collectDemoOutputs(payload: Record<string, unknown>): DemoJobOutput[] {
  const job = recordValue(payload.job)
  const candidates = [payload.outputs, job?.outputs, payload.output, job?.output, payload.media, job?.media]
  const outputs: DemoJobOutput[] = []
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      candidate.forEach((entry) => {
        const item = recordValue(entry)
        if (item) outputs.push(item as DemoJobOutput)
      })
      continue
    }
    const item = recordValue(candidate)
    if (item) outputs.push(item as DemoJobOutput)
  }
  if (job && stringValue(job.media_url)) outputs.push(job as DemoJobOutput)
  return outputs
}

function readDemoJobResult(payload: Record<string, unknown>) {
  const job = recordValue(payload.job)
  const jobError = recordValue(job?.error)
  const responseStatus = stringValue(payload.status)?.toUpperCase()
  return {
    responseStatus,
    status: stringValue(job?.status)?.toUpperCase() ?? responseStatus ?? 'UNKNOWN',
    jobId: stringValue(job?.id),
    promptId: stringValue(job?.prompt_id),
    outputs: collectDemoOutputs(payload),
    reasonCode: stringValue(payload.reason_code) ?? stringValue(job?.reason_code) ?? stringValue(jobError?.reason_code),
  }
}

function isVerifiedMp4Output(output: DemoJobOutput): boolean {
  if (output.verified !== true || !stringValue(output.media_url)) return false
  const mime = stringValue(output.mime)?.toLowerCase()
  const mp4Name = [output.filename, output.path, output.media_url]
    .filter((value): value is string => Boolean(stringValue(value)))
    .some((value) => value.split('?')[0].toLowerCase().endsWith('.mp4'))
  return mime?.startsWith('video/mp4') === true || mp4Name
}

function verifiedDemoVideo(outputs?: DemoJobOutput[]): DemoJobOutput | null {
  return outputs?.find(isVerifiedMp4Output) ?? null
}

function shortHash(value?: string): string | null {
  return value && value.length >= 12 ? `${value.slice(0, 12)}...` : value ?? null
}

function displayDuration(output: DemoJobOutput): string | null {
  const seconds = numberValue(output.duration_seconds) ?? numberValue(output.duration)
  return seconds && seconds > 0 ? `${seconds.toFixed(seconds % 1 === 0 ? 0 : 1)} 秒` : null
}

function stableDemoIdempotencyKey(lane: DemoLane, shotId: string): string {
  const storageKey = `comfystudio-v44-demo:${lane}:${shotId}`
  try {
    const existing = window.sessionStorage.getItem(storageKey)
    if (existing) return existing
    const nonce = window.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    const next = `v44-${lane}-${shotId}-${nonce}`
    window.sessionStorage.setItem(storageKey, next)
    return next
  } catch {
    return `v44-${lane}-${shotId}`
  }
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const raw = await response.text()
  let payload: unknown = null
  if (raw) {
    try {
      payload = JSON.parse(raw)
    } catch {
      payload = raw
    }
  }
  if (!response.ok) throw new ApiError(response.status, response.statusText, payload)
  return payload as T
}

async function tryCandidates<T>(urls: string[], init?: RequestInit): Promise<{ data: T; url: string }> {
  let lastError: unknown = new Error('No API candidate available')
  for (const url of urls) {
    try {
      return { data: await requestJson<T>(url, init), url }
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) throw error
      lastError = error
    }
  }
  throw lastError
}

function normalizeAssets(payload: unknown): Asset[] {
  if (Array.isArray(payload)) return payload as Asset[]
  if (payload && typeof payload === 'object') {
    const object = payload as Record<string, unknown>
    for (const key of ['assets', 'items', 'data']) {
      if (Array.isArray(object[key])) return object[key] as Asset[]
    }
  }
  return []
}

function normalizeCanvas(payload: unknown): CanvasPayload | null {
  if (!payload || typeof payload !== 'object') return null
  const source = payload as Record<string, unknown>
  const nested = source.canvas && typeof source.canvas === 'object' ? (source.canvas as Record<string, unknown>) : source
  if (!Array.isArray(nested.nodes) || !Array.isArray(nested.edges)) return null
  return {
    nodes: nested.nodes as StudioNode[],
    edges: nested.edges as Edge[],
    viewport: nested.viewport as Viewport | undefined,
    revision: typeof nested.revision === 'number' ? nested.revision : undefined,
    updatedAt: typeof nested.updatedAt === 'string'
      ? nested.updatedAt
      : typeof nested.updated_at === 'string'
        ? nested.updated_at
        : undefined,
    bindings: Array.isArray(nested.bindings) ? nested.bindings as ReferenceBinding[] : [],
  }
}

function canConnect(source: StudioNode | undefined, target: StudioNode | undefined, nodes: StudioNode[], edges: Edge[]): boolean {
  if (!source || !target || source.id === target.id) return false
  const allowedTargets = CANON_RULES[source.data.kind] ?? []
  if (!allowedTargets.includes(target.data.kind)) return false

  // A directed path from target back to source would create a cycle.
  const visited = new Set<string>()
  const pending = [target.id]
  while (pending.length) {
    const id = pending.shift() as string
    if (id === source.id) return false
    if (visited.has(id)) continue
    visited.add(id)
    edges.filter((edge) => edge.source === id).forEach((edge) => pending.push(edge.target))
  }
  return true
}

function StudioNodeCard({ data, selected }: NodeProps<StudioNode>) {
  const state = data.state ?? 'idle'
  return (
    <div className={`studio-node-card node-${data.kind} ${selected ? 'is-selected' : ''}`}>
      <Handle className="node-handle" type="target" position={Position.Left} id="in" />
      <div className="node-card-topline">
        <span className="node-kind">{NODE_LABELS[data.kind]}</span>
        <span className={`node-state state-${state}`}>{stateLabel[state]}</span>
      </div>
      <strong>{data.label}</strong>
      <span className="node-summary">{data.summary || NODE_DESCRIPTIONS[data.kind]}</span>
      {data.assetId && <span className="node-id">{data.assetId}</span>}
      <Handle className="node-handle" type="source" position={Position.Right} id="out" />
    </div>
  )
}

const nodeTypes = { studio: StudioNodeCard }

function AppInner() {
  const reactFlow = useReactFlow<StudioNode>()
  const [nodes, setNodes] = useState<StudioNode[]>(starterNodes)
  const [edges, setEdges] = useState<Edge[]>(starterEdges)
  const [assets, setAssets] = useState<Asset[]>([])
  const [selectedId, setSelectedId] = useState<string | null>('shot-001')
  const [health, setHealth] = useState<HealthState>({ studio: 'checking', comfy: 'unknown', label: '正在检查服务' })
  const [status, setStatus] = useState('准备就绪')
  const [revision, setRevision] = useState(0)
  const [viewport, setViewport] = useState<Viewport>({ x: 0, y: 0, zoom: 1 })
  const [bindings, setBindings] = useState<ReferenceBinding[]>([])
  const [referenceRole, setReferenceRole] = useState<ReferenceRole>('character_identity')
  const [referenceAssetId, setReferenceAssetId] = useState('')
  const [busy, setBusy] = useState(false)
  const [mode, setMode] = useState<StudioMode>('director')
  const [demoProject, setDemoProject] = useState<DemoProjectPayload | null>(null)
  const [demoShotId, setDemoShotId] = useState('SHOT001')
  const [demoLane, setDemoLane] = useState<DemoLane>('local_comfy')
  const [demoActionBusy, setDemoActionBusy] = useState(false)
  const [demoJobPolling, setDemoJobPolling] = useState(false)
  const [demoRuntimeOverrides, setDemoRuntimeOverrides] = useState<Record<string, DemoRuntimeShot>>({})
  const [demoFeedback, setDemoFeedback] = useState<DemoFeedback | null>(null)
  const demoProjectLoadedRef = useRef(false)
  const demoPollingJobRef = useRef<string | null>(null)

  const selectedNode = useMemo(() => nodes.find((node) => node.id === selectedId) ?? null, [nodes, selectedId])
  const selectedDemoShot = useMemo(() => demoProject?.shots.find((shot) => shot.id === demoShotId), [demoProject, demoShotId])
  const demoRuntime = demoRuntimeOverrides[demoShotId] ?? (demoProject?.runtime?.shots?.[demoShotId] as DemoRuntimeShot | undefined)
  const demoVideo = useMemo(() => verifiedDemoVideo(demoRuntime?.outputs), [demoRuntime?.outputs])
  const demoReady = Boolean(demoProject)
  const demoShots: DemoShot[] = demoProject?.shots ?? [
    { id: 'SHOT001', title: 'SHOT001', duration_seconds: 0, scene: '', scene_text: '', output: 'SHOT001.mp4' },
    { id: 'SHOT002', title: 'SHOT002', duration_seconds: 0, scene: '', scene_text: '', output: 'SHOT002.mp4' },
  ]

  const refreshDemoProject = useCallback(async () => {
    try {
      const data = await requestJson<DemoProjectPayload>('/api/v10/demo/project')
      setDemoProject(data)
      if (Array.isArray(data.assets) && data.assets.length) {
        setAssets((current) => {
          const merged = new Map(current.map((asset) => [asset.id, asset]))
          data.assets?.forEach((asset) => merged.set(asset.id, asset))
          return [...merged.values()]
        })
      }
      const shotIds = data.shots.map((shot) => shot.id)
      const defaultShotId = data.project.default_shot_id ?? shotIds[0]
      const firstLoad = !demoProjectLoadedRef.current
      demoProjectLoadedRef.current = true
      setDemoShotId((current) => {
        if (firstLoad && defaultShotId) return defaultShotId
        return shotIds.includes(current) ? current : (defaultShotId ?? current)
      })
    } catch {
      setStatus('Demo 项目未加载')
    }
  }, [])

  const prepareDemoShot = useCallback(async () => {
    setDemoActionBusy(true)
    try {
      const data = await requestJson<Record<string, unknown>>(`/api/v10/demo/shots/${demoShotId}/prepare`)
      if (data.status === 'READY') {
        setStatus(`${demoShotId} 资产、Canon、连续性预检通过`)
        setDemoFeedback({ tone: 'success', title: `${demoShotId} 预检通过`, detail: '资产、Canon 与连续性检查已完成。' })
      } else {
        const reason = summarizeApiPayload(data, '请查看 Canon/连续性问题')
        setStatus(`${demoShotId} 预检阻断 · ${reason}`)
        setDemoFeedback({ tone: 'blocked', title: `${demoShotId} 已阻断`, detail: reason })
      }
    } catch (error) {
      setStatus(formatApiError(error, `${demoShotId} 预检失败`))
      setDemoFeedback({ tone: 'failed', title: `${demoShotId} 预检失败`, detail: formatApiError(error, '无法读取预检结果') })
    } finally {
      setDemoActionBusy(false)
    }
  }, [demoShotId])

  const pollDemoJob = useCallback(async (shotId: string, jobId: string) => {
    if (demoPollingJobRef.current === jobId) return
    demoPollingJobRef.current = jobId
    setDemoJobPolling(true)
    try {
      for (let attempt = 0; attempt < 30; attempt += 1) {
        if (attempt > 0) await new Promise((resolve) => window.setTimeout(resolve, 2000))
        try {
          const data = await requestJson<Record<string, unknown>>(`/api/v10/jobs/${encodeURIComponent(jobId)}/refresh`, { method: 'POST' })
          const result = readDemoJobResult(data)
          const state = result.status
          setDemoRuntimeOverrides((current) => ({
            ...current,
            [shotId]: { status: state, job_id: result.jobId ?? jobId, prompt_id: result.promptId, outputs: result.outputs, reason_code: result.reasonCode },
          }))
          setStatus(`${shotId} ${demoStatusLabel(state)}${result.outputs.length ? ` · ${result.outputs.length} 个输出` : ''}`)
          await refreshDemoProject()
          if (!TERMINAL_DEMO_JOB_STATUSES.has(state)) continue

          const video = verifiedDemoVideo(result.outputs)
          if (state === 'SUCCEEDED' && video) {
            setDemoFeedback({ tone: 'success', title: `${shotId} 已取得已验证 MP4`, detail: `Job ${result.jobId ?? jobId} 已完成，可在下方播放。` })
          } else if (state === 'SUCCEEDED') {
            setDemoFeedback({ tone: 'blocked', title: `${shotId} 未取得可验证 MP4`, detail: 'Job 已终态，但返回结果没有已验证的 MP4 media_url；不会显示播放器。' })
          } else {
            setDemoFeedback({ tone: 'failed', title: `${shotId} ${demoStatusLabel(state)}`, detail: result.reasonCode ?? summarizeApiPayload(data, '请检查 Job 事件与 Worker 状态。') })
          }
          return
        } catch (error) {
          setStatus(formatApiError(error, `${shotId} 状态回收失败`))
          setDemoFeedback({ tone: 'failed', title: `${shotId} 状态回收失败`, detail: formatApiError(error, '未能刷新已创建 Job') })
          return
        }
      }
      setStatus(`${shotId} 已提交并持续排队，尚未取得最终 MP4 证据`)
      setDemoFeedback({ tone: 'working', title: `${shotId} 仍在执行`, detail: '已持续刷新既有 Job；未再次提交生成请求。' })
    } finally {
      if (demoPollingJobRef.current === jobId) demoPollingJobRef.current = null
      setDemoJobPolling(false)
    }
  }, [refreshDemoProject])

  const refreshCreatedDemoJob = useCallback(async () => {
    const jobId = demoRuntime?.job_id
    if (!jobId || demoJobPolling) return
    setDemoActionBusy(true)
    try {
      await pollDemoJob(demoShotId, jobId)
    } finally {
      setDemoActionBusy(false)
    }
  }, [demoJobPolling, demoRuntime?.job_id, demoShotId, pollDemoJob])

  const generateDemoShot = useCallback(async () => {
    if (demoLane !== 'local_comfy') {
      const laneLabel = demoLane === 'AutoDL5090' ? 'AutoDL 5090' : 'API'
      const detail = `${laneLabel} 尚未配置，未发送外部或付费请求，也不会回退到本机 ComfyUI。`
      setStatus(`BLOCKED · ${detail}`)
      setDemoFeedback({ tone: 'blocked', title: `${laneLabel} 已阻断`, detail })
      return
    }
    setDemoActionBusy(true)
    const shotId = demoShotId
    try {
      const data = await requestJson<Record<string, unknown>>(`/api/v10/demo/shots/${shotId}/generate`, {
        method: 'POST',
        body: JSON.stringify({ execute: true, lane: demoLane, idempotency_key: stableDemoIdempotencyKey(demoLane, shotId) }),
      })
      const result = readDemoJobResult(data)
      if (result.responseStatus === 'BLOCKED' || result.responseStatus === 'HOLD') {
        const reason = result.reasonCode ?? summarizeApiPayload(data, '请查看 Canon、Capsule 或 Worker 预检。')
        setStatus(`BLOCKED · ${shotId} ${reason}`)
        setDemoFeedback({ tone: 'blocked', title: `${shotId} 已阻断`, detail: reason })
        return
      }
      if (result.responseStatus === 'FAILED' || result.status === 'FAILED') {
        const reason = result.reasonCode ?? summarizeApiPayload(data, 'ComfyUI 未接受此生成请求。')
        setStatus(`FAILED · ${shotId} ${reason}`)
        setDemoFeedback({ tone: 'failed', title: `${shotId} 生成失败`, detail: reason })
        return
      }
      if (result.jobId) {
        setDemoRuntimeOverrides((current) => ({
          ...current,
          [shotId]: { status: result.status, job_id: result.jobId, prompt_id: result.promptId, outputs: result.outputs, reason_code: result.reasonCode },
        }))
        const replay = result.responseStatus === 'IDEMPOTENT_REPLAY'
        setStatus(replay ? `${shotId} 已恢复既有 Job ${result.jobId}` : `${shotId} 已提交本机 ComfyUI，任务 ${result.jobId}`)
        setDemoFeedback({
          tone: 'working',
          title: replay ? `${shotId} 已恢复既有 Job` : `${shotId} 已提交`,
          detail: replay ? '检测到相同幂等键，系统将只刷新已有 Job，不会再次提交。' : '已创建 Durable Job，正在刷新其状态。',
        })
      } else {
        setStatus(`${shotId}：${result.responseStatus ?? 'UNKNOWN'}`)
        setDemoFeedback({ tone: 'blocked', title: `${shotId} 未创建 Job`, detail: summarizeApiPayload(data, '服务没有返回可刷新的 Job ID。') })
      }
      await refreshDemoProject()
      if (result.jobId) void pollDemoJob(shotId, result.jobId)
    } catch (error) {
      const detail = formatApiError(error, `${shotId} 生成被阻断，请查看 Canon 或 Worker 状态`)
      setStatus(detail)
      const blocked = error instanceof ApiError && recordValue(error.payload)?.status === 'BLOCKED'
      setDemoFeedback({ tone: blocked ? 'blocked' : 'failed', title: blocked ? `${shotId} 已阻断` : `${shotId} 生成失败`, detail })
    } finally {
      setDemoActionBusy(false)
    }
  }, [demoLane, demoShotId, pollDemoJob, refreshDemoProject])
  const refreshAssets = useCallback(async () => {
    try {
      const { data } = await tryCandidates<unknown>(API_CANDIDATES.assets)
      setAssets(normalizeAssets(data))
    } catch {
      setAssets([
        { id: 'CHAR_SW45_MASTER', type: 'character', name: '苏晚晴45岁', tags: ['face', 'age', 'voice'] },
        { id: 'CHAR_SW25_MASTER', type: 'character', name: '苏晚晴25岁', tags: ['face', 'age'] },
        { id: 'SCENE_2006_STUDIO', type: 'scene', name: '2006设计工作室' },
        { id: 'PROP_PHONE_2006', type: 'prop', name: '米黄色有线座机' },
      ])
    }
  }, [])

  useEffect(() => {
    if (!referenceAssetId && assets[0]) setReferenceAssetId(assets[0].id)
  }, [assets, referenceAssetId])

  const refreshHealth = useCallback(async () => {
    try {
      const { data } = await tryCandidates<Record<string, unknown>>(API_CANDIDATES.health)
      const comfyValue = data.comfy ?? data.comfyui ?? data.comfy_status
      const comfyOnline = typeof comfyValue === 'object'
        ? Boolean((comfyValue as Record<string, unknown>).connected ?? (comfyValue as Record<string, unknown>).ok ?? (comfyValue as Record<string, unknown>).online ?? ((comfyValue as Record<string, unknown>).status === 200))
        : Boolean(comfyValue)
      setHealth({ studio: 'online', comfy: comfyOnline ? 'online' : 'offline', label: comfyOnline ? 'StudioOS + ComfyUI 在线' : 'StudioOS 在线 · ComfyUI 待机' })
    } catch {
      setHealth({ studio: 'offline', comfy: 'unknown', label: 'StudioOS 未连接' })
    }
  }, [])

  const loadCanvas = useCallback(async () => {
    setBusy(true)
    try {
      const { data } = await tryCandidates<unknown>(API_CANDIDATES.canvas)
      const canvas = normalizeCanvas(data)
      if (!canvas) throw new Error('Canvas payload invalid')
      const hasGraph = canvas.nodes.length > 0 || canvas.edges.length > 0
      setNodes(hasGraph ? canvas.nodes : starterNodes)
      setEdges(hasGraph ? canvas.edges : starterEdges)
      if (canvas.viewport) {
        setViewport(canvas.viewport)
        reactFlow.setViewport(canvas.viewport)
      }
      setRevision(canvas.revision ?? 0)
      setBindings(canvas.bindings ?? [])
      setStatus(hasGraph ? `已加载导演台 · 版本 ${canvas.revision ?? 0}` : '已加载起始导演流程 · 可拖拽连线')
    } catch {
      const local = localStorage.getItem('comfystudio-director-canvas')
      if (local) {
        try {
          const canvas = normalizeCanvas(JSON.parse(local))
          if (canvas) {
            setNodes(canvas.nodes)
            setEdges(canvas.edges)
            setStatus('已从本机缓存恢复画布')
          }
        } catch {
          setStatus('后端画布未响应，使用起始模板')
        }
      } else {
        setStatus('后端画布未响应，使用起始模板')
      }
    } finally {
      setBusy(false)
    }
  }, [reactFlow])

  useEffect(() => {
    void refreshAssets()
    void refreshHealth()
    void loadCanvas()
    void refreshDemoProject()
  }, [loadCanvas, refreshAssets, refreshHealth, refreshDemoProject])

  const onNodesChange = useCallback((changes: NodeChange<StudioNode>[]) => {
    setNodes((current) => applyNodeChanges(changes, current) as StudioNode[])
  }, [])

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((current) => applyEdgeChanges(changes, current))
  }, [])

  const onConnect: OnConnect = useCallback((connection: Connection) => {
    const source = nodes.find((node) => node.id === connection.source)
    const target = nodes.find((node) => node.id === connection.target)
    if (!canConnect(source, target, nodes, edges)) {
      setStatus('连接被拒绝：节点类型不兼容或会形成环路')
      return
    }
    setEdges((current) => addEdge({ ...connection, type: 'smoothstep', animated: true }, current))
    setStatus(`已连接 ${source?.data.label} → ${target?.data.label}`)
  }, [edges, nodes])

  const addAssetNode = useCallback((asset: Asset, position?: { x: number; y: number }) => {
    const kind = (['character', 'scene', 'prop', 'audio'].includes(asset.type) ? asset.type : 'asset') as NodeKind
    const next: StudioNode = {
      id: `asset-${asset.id}-${Date.now()}`,
      type: 'studio',
      position: position ?? { x: 100 + (nodes.length % 3) * 260, y: 80 + (nodes.length % 4) * 150 },
      data: { label: asset.name, kind, assetId: asset.id, assetType: asset.type, state: 'ready', summary: asset.description || `${asset.type} asset` },
    }
    setNodes((current) => [...current, next])
    setSelectedId(next.id)
    setStatus(`已添加资产：${asset.name}`)
  }, [nodes.length])

  const onDrop = useCallback((event: DragEvent) => {
    event.preventDefault()
    const raw = event.dataTransfer.getData('application/comfystudio-asset')
    if (!raw) return
    try {
      const asset = JSON.parse(raw) as Asset
      addAssetNode(asset, reactFlow.screenToFlowPosition({ x: event.clientX, y: event.clientY }))
    } catch {
      setStatus('资产数据无法读取')
    }
  }, [addAssetNode, reactFlow])

  const saveCanvas = useCallback(async () => {
    setBusy(true)
    // The server owns the next revision.  Send the revision last loaded by this
    // client so its compare-and-swap guard can reject stale edits deterministically.
    const payload: CanvasPayload = { nodes, edges, viewport, revision, bindings }
    localStorage.setItem('comfystudio-director-canvas', JSON.stringify(payload))
    try {
      let saved: CanvasPayload | null = null
      let url = ''
      for (const method of ['PUT', 'POST'] as const) {
        try {
          const response = await tryCandidates<CanvasPayload>(API_CANDIDATES.canvas, { method, body: JSON.stringify(payload) })
          url = response.url
          saved = response.data
          break
        } catch (error) {
          if (error instanceof ApiError && error.status === 409) throw error
          // Some v10 deployments expose the canvas as POST-only; continue to the next method.
        }
      }
      if (!url) {
        const response = await tryCandidates<CanvasPayload>(['/director/canvas/save'], { method: 'POST', body: JSON.stringify(payload) })
        url = response.url
        saved = response.data
      }
      const serverRevision = saved && typeof saved.revision === 'number' ? saved.revision : revision + 1
      setRevision(serverRevision)
      setStatus(`已保存导演台 · Revision ${serverRevision} · ${url}`)
    } catch (error) {
      setStatus(error instanceof ApiError && error.status === 409
        ? '保存冲突：服务端画布版本已变化，请先重新加载再保存'
        : '已保存到本机缓存，服务端接口待连接')
    } finally {
      setBusy(false)
    }
  }, [bindings, edges, nodes, revision, viewport])

  const bindReference = useCallback((asset: Asset, role: ReferenceRole = referenceRole) => {
    setBindings((current) => {
      const filtered = current.filter((item) => item.role !== role)
      return [...filtered, { id: `binding-${role}-${asset.id}`, assetId: asset.id, assetName: asset.name, role, enabled: true, sourceShot: demoShotId }]
    })
    setStatus(`已绑定${REFERENCE_ROLES.find((item) => item.id === role)?.label ?? '参考'}：${asset.name}`)
  }, [demoShotId, referenceRole])

  const removeBinding = useCallback((bindingId: string) => {
    setBindings((current) => current.filter((item) => item.id !== bindingId))
    setStatus('已移除参考绑定')
  }, [])

  const runCanon = useCallback(async () => {
    setBusy(true)
    const shotNode = selectedNode?.data.kind === 'shot' ? selectedNode : nodes.find((node) => node.data.kind === 'shot')
    const shot = shotNode ? { ...(selectedDemoShot ?? {}), id: selectedDemoShot?.id ?? shotNode.id, ...shotNode.data } : selectedDemoShot ?? null
    const references = bindings.filter((binding) => binding.enabled).map((binding) => ({ ...binding, asset: assets.find((asset) => asset.id === binding.assetId) }))
    try {
      const { data } = await tryCandidates<Record<string, unknown>>(API_CANDIDATES.canon, { method: 'POST', body: JSON.stringify({ shot, nodes, edges, bindings, references, assets }) })
      const blocked = data.blocked === true || data.pass === false || data.ok === false
      setNodes((current) => current.map((node) => node.id === shotNode?.id ? { ...node, data: { ...node.data, state: blocked ? 'blocked' : 'ready' } } : node))
      setStatus(blocked ? `Canon 阻断 · ${summarizeApiPayload(data, '请修正年代、人物或道具冲突')}` : 'Canon 检查通过')
    } catch (error) {
      setStatus(formatApiError(error, 'Canon 服务未连接，未改变生成状态'))
    } finally {
      setBusy(false)
    }
  }, [assets, bindings, edges, nodes, selectedDemoShot, selectedNode])

  const compilePrompt = useCallback(async () => {
    setBusy(true)
    const shotNode = selectedNode?.data.kind === 'shot' ? selectedNode : nodes.find((node) => node.data.kind === 'shot')
    const shot = shotNode ? { ...(selectedDemoShot ?? {}), id: selectedDemoShot?.id ?? shotNode.id, ...shotNode.data } : selectedDemoShot ?? null
    const references = bindings.filter((binding) => binding.enabled).map((binding) => ({ ...binding, asset: assets.find((asset) => asset.id === binding.assetId) }))
    try {
      const { data } = await tryCandidates<Record<string, unknown>>(API_CANDIDATES.prompt, { method: 'POST', body: JSON.stringify({ shot, nodes, edges, bindings, references, assets, memory: { demo_shot_id: demoShotId } }) })
      const positive = typeof data.positive === 'string' ? data.positive : typeof data.positive_prompt === 'string' ? data.positive_prompt : 'Prompt ready'
      setNodes((current) => current.map((node) => node.data.kind === 'prompt' ? { ...node, data: { ...node.data, state: 'ready', summary: positive.slice(0, 90) } } : node))
      setStatus('Prompt Compiler 已生成正向与负向提示词')
    } catch (error) {
      setStatus(formatApiError(error, 'Prompt Compiler 服务未连接'))
    } finally {
      setBusy(false)
    }
  }, [assets, bindings, demoShotId, edges, nodes, selectedDemoShot, selectedNode])

  const onNodeClick = useCallback((_: MouseEvent, node: StudioNode) => setSelectedId(node.id), [])

  return (
    <div className="studio-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">CS</div>
          <div>
            <strong>ComfyStudio</strong>
            <span>StudioOS Production Core</span>
          </div>
        </div>
        <div className="topbar-meta">
          <span className={`health-dot health-${health.studio}`} />
          <span>{health.label}</span>
          <span className="endpoint">导演模式 · 8190 / 8189</span>
          <div className="mode-switch" role="group" aria-label="工作模式">
            <button className={mode === 'director' ? 'mode-active' : ''} onClick={() => setMode('director')}>导演</button>
            <button className={mode === 'engineering' ? 'mode-active' : ''} onClick={() => setMode('engineering')}>工程</button>
          </div>
          <button className="button button-quiet" onClick={() => { void refreshHealth() }} disabled={busy}>刷新状态</button>
          <button className="button button-primary" onClick={() => { void saveCanvas() }} disabled={busy}>保存导演台</button>
        </div>
      </header>

      <section className="demo-strip" aria-label="Director Production Demo">
        <div className="demo-project-copy">
          <span className="eyebrow">Director Production Demo</span>
          <strong>{demoProject?.project.title ?? '楼上是25岁的我，楼下是未来女儿'}</strong>
          <small>自动资产解析 · Canon · 连续性 · H3 Worker</small>
        </div>
        <div className="demo-shot-tabs">
          {demoShots.map((shot) => (
            <button key={shot.id} className={demoShotId === shot.id ? 'demo-shot-active' : ''} onClick={() => setDemoShotId(shot.id)}>
              <span className="demo-shot-label"><strong>{shot.id}</strong><em className={`demo-shot-status status-${demoStatusClass((demoRuntimeOverrides[shot.id] ?? demoProject?.runtime?.shots?.[shot.id])?.status ?? shot.status)}`}>{demoStatusLabel((demoRuntimeOverrides[shot.id] ?? demoProject?.runtime?.shots?.[shot.id])?.status ?? shot.status)}</em></span>
              <small>{shot.title}</small>
            </button>
          ))}
        </div>
        <div className="demo-actions">
          <select className="demo-lane-select" aria-label="生成通道" value={demoLane} onChange={(event) => setDemoLane(event.target.value as DemoLane)} disabled={demoActionBusy || demoJobPolling}>
            <option value="local_comfy">本机 ComfyUI 8189</option>
            <option value="AutoDL5090">AutoDL 5090</option>
            <option value="API">API</option>
          </select>
          <span className="demo-runtime-note">{demoRuntime?.job_id ? `Job ${demoRuntime.job_id}` : demoReady ? `${demoStatusLabel(demoRuntime?.status ?? selectedDemoShot?.status)}` : '等待 StudioOS'}</span>
          <button className="button button-quiet" onClick={() => { void prepareDemoShot() }} disabled={demoActionBusy || !demoReady}>预检镜头</button>
          <button className="button button-quiet" onClick={() => { void refreshCreatedDemoJob() }} disabled={demoActionBusy || demoJobPolling || !demoRuntime?.job_id}>刷新任务</button>
          <button className="button button-primary" onClick={() => { void generateDemoShot() }} disabled={demoActionBusy || demoJobPolling || !demoReady}>生成镜头</button>
        </div>
        {demoFeedback && <div className={`demo-feedback feedback-${demoFeedback.tone}`} role="status"><strong>{demoFeedback.title}</strong>{demoFeedback.detail && <span>{demoFeedback.detail}</span>}</div>}
        {demoVideo && <div className="demo-video-evidence" aria-label="已验证的视频输出">
          <video controls preload="metadata">
            <source src={demoVideo.media_url} type="video/mp4" />
            浏览器无法播放该已验证 MP4。
          </video>
          <div className="demo-video-meta">
            <span className="eyebrow">已验证 MP4</span>
            <strong>{demoShotId} 输出</strong>
            <small>{displayDuration(demoVideo) ?? '时长待服务回传'}{shortHash(demoVideo.sha256) ? ` · SHA-256 ${shortHash(demoVideo.sha256)}` : ''}</small>
            <small>{demoRuntime?.job_id ? `Job ${demoRuntime.job_id}` : '已绑定当前 Job'}</small>
          </div>
        </div>}
      </section>
      <main className="workspace">
        <aside className="asset-rail">
          <div className="panel-heading">
          <div>
              <span className="eyebrow">资产管理</span>
              <h2>资产库</h2>
            </div>
            <span className="count-badge">{assets.length}</span>
          </div>
          <p className="panel-copy">拖拽角色、场景和道具到画布，资产会保留 Canon 关联。</p>
          <div className="asset-list">
            {assets.map((asset) => (
              <button
                className="asset-item"
                key={asset.id}
                draggable
                onDragStart={(event) => event.dataTransfer.setData('application/comfystudio-asset', JSON.stringify(asset))}
                onClick={() => addAssetNode(asset)}
              >
                <span className={`asset-icon asset-${asset.type}`}>{asset.type.slice(0, 1).toUpperCase()}</span>
                <span className="asset-copy"><strong>{asset.name}</strong><small>{ASSET_TYPE_LABELS[asset.type] ?? asset.type} · {asset.id}</small></span>
                <span className="asset-add">+</span>
              </button>
            ))}
          </div>
          <section className="reference-panel" aria-label="全能参考">
            <div className="panel-heading reference-heading"><div><span className="eyebrow">参考绑定</span><h2>全能参考</h2></div><span className="count-badge">{bindings.length}</span></div>
            <p className="panel-copy">把角色、场景、道具和上一镜素材绑定到当前镜头。预检时才生成 Mixed 编号。</p>
            <div className="reference-controls">
              <select aria-label="参考角色" value={referenceRole} onChange={(event) => setReferenceRole(event.target.value as ReferenceRole)}>
                {REFERENCE_ROLES.map((role) => <option key={role.id} value={role.id}>{role.label}</option>)}
              </select>
              <select aria-label="参考资产" value={referenceAssetId} onChange={(event) => setReferenceAssetId(event.target.value)}>
                {assets.map((asset) => <option key={asset.id} value={asset.id}>{asset.name}</option>)}
              </select>
              <button className="button button-primary reference-bind" onClick={() => { const asset = assets.find((item) => item.id === referenceAssetId); if (asset) bindReference(asset) }} disabled={!referenceAssetId || busy}>绑定</button>
            </div>
            <div className="reference-presets">
              <button className="preset-chip" onClick={() => setReferenceRole('character_identity')}>人物连续性</button>
              <button className="preset-chip" onClick={() => setReferenceRole('previous_video')}>镜头续接</button>
              <button className="preset-chip" onClick={() => setReferenceRole('scene')}>2 图 + 1 视频</button>
            </div>
            <div className="binding-list">
              {bindings.length === 0 ? <span className="binding-empty">尚未绑定参考素材</span> : bindings.map((binding) => (
                <div className="binding-item" key={binding.id}>
                  <div><strong>{REFERENCE_ROLES.find((role) => role.id === binding.role)?.label}</strong><small>{binding.assetName}</small></div>
                  <button className="binding-remove" aria-label={`移除${binding.assetName}`} onClick={() => removeBinding(binding.id)}>×</button>
                </div>
              ))}
            </div>
          </section>
          <div className="node-palette">
            <div className="palette-heading">导演节点</div>
            {(['shot', 'prompt', 'model', 'output'] as NodeKind[]).map((kind) => (
              <button className="palette-item" key={kind} onClick={() => {
                const next: StudioNode = { id: `${kind}-${Date.now()}`, type: 'studio', position: { x: 250 + nodes.length * 18, y: 120 + nodes.length * 12 }, data: { label: NODE_LABELS[kind], kind, state: 'idle' } }
                setNodes((current) => [...current, next]); setSelectedId(next.id)
              }}>
                <span className={`palette-dot dot-${kind}`} />{NODE_LABELS[kind]}<span>+</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="canvas-panel">
          <div className="canvas-toolbar">
            <div><span className="eyebrow">{mode === 'director' ? '导演流程' : '工程连线'}</span><h1>{mode === 'director' ? '导演台' : '工程连线台'}</h1></div>
            <div className="flow-toolbar-actions">
              <button className="button button-quiet" onClick={() => { void loadCanvas() }} disabled={busy}>加载画布</button>
              <span className="revision">版本 {revision}</span>
            </div>
          </div>
          <div className="flow-canvas" onDrop={onDrop} onDragOver={(event) => event.preventDefault()}>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={() => setSelectedId(null)}
              onMoveEnd={(_, nextViewport) => setViewport(nextViewport)}
              fitView
              fitViewOptions={{ padding: 0.18, minZoom: 0.45, maxZoom: 1.1 }}
              connectionLineStyle={{ stroke: '#76a9ff', strokeWidth: 2 }}
              isValidConnection={(connection) => canConnect(nodes.find((node) => node.id === connection.source), nodes.find((node) => node.id === connection.target), nodes, edges)}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#273142" gap={24} variant={BackgroundVariant.Dots} />
              <Controls showInteractive={false} />
              <MiniMap nodeColor={(node) => `var(--node-${(node.data as StudioNodeData).kind}, #6d7d98)`} maskColor="rgba(8, 12, 19, .72)" />
            </ReactFlow>
            <div className="canvas-hint">拖入资产 · 从左到右连接 · 不允许环路 · 当前{mode === 'director' ? '导演' : '工程'}模式</div>
          </div>
          <div className="statusbar"><span className={`health-dot health-${health.comfy}`} /><span>{status}</span><span className="status-spacer" /><span>{nodes.length} 个节点 · {edges.length} 条连线</span></div>
        </section>

        <aside className="inspector-rail">
          <div className="panel-heading"><div><span className="eyebrow">属性与门禁</span><h2>节点检查器</h2></div></div>
          {selectedNode ? (
            <div className="inspector-content">
              <div className={`inspector-badge node-${selectedNode.data.kind}`}><span>{NODE_LABELS[selectedNode.data.kind]}</span><span>{stateLabel[selectedNode.data.state ?? 'idle']}</span></div>
              <h3>{selectedNode.data.label}</h3>
              <p>{selectedNode.data.summary || NODE_DESCRIPTIONS[selectedNode.data.kind]}</p>
              {selectedNode.data.assetId && <div className="field-row"><span>资产 ID</span><code>{selectedNode.data.assetId}</code></div>}
              <div className="inspector-actions">
                <button className="action-button" onClick={() => { void runCanon() }} disabled={busy}><span className="action-icon">✓</span>Canon 检查</button>
                <button className="action-button" onClick={() => { void compilePrompt() }} disabled={busy}><span className="action-icon">✦</span>编译提示词</button>
              </div>
              <div className="inspector-note"><strong>流程状态</strong><span>镜头 → 提示词 → 模型 → 结果</span><small>连接校验已启用，Canon 阻断会锁住生成入口。</small></div>
            </div>
          ) : <div className="empty-inspector">选择一个节点查看导演上下文。</div>}
          <div className="service-card"><div className="service-card-title">运行时</div><div className="service-line"><span>StudioOS</span><span className={`service-state state-${health.studio}`}>{health.studio === 'online' ? '在线' : '离线'}</span></div><div className="service-line"><span>ComfyUI</span><span className={`service-state state-${health.comfy}`}>{health.comfy === 'online' ? '在线' : health.comfy === 'offline' ? '离线' : '未知'}</span></div></div>
        </aside>
      </main>
    </div>
  )
}

function App() {
  return <ReactFlowProvider><AppInner /></ReactFlowProvider>
}

createRoot(document.getElementById('root')!).render(<App />)


