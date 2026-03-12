import { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const TABS = [
  {
    key: 'deepfake',
    emoji: '🖼️',
    label: 'Deepfake Detector',
    endpoint: '/api/analyze/deepfake',
    button: 'Analyze Image',
    helper: 'Detect manipulated, deepfake, or fully AI-generated visuals.'
  },
  {
    key: 'handwriting',
    emoji: '✍️',
    label: 'Handwriting Analyzer',
    endpoint: '/api/analyze/handwriting',
    button: 'Analyze Writing',
    helper: 'Identify human handwriting vs AI-simulated text patterns.'
  },
  {
    key: 'fake-news',
    emoji: '📰',
    label: 'Fake News Detector',
    endpoint: '/api/analyze/fake-news',
    button: 'Fact-Check Now',
    helper: 'Extract headline claims and assess credibility signals.'
  }
]

const riskToPercent = {
  LOW: 25,
  MEDIUM: 60,
  HIGH: 95
}

function ProgressBar({ label, value, color }) {
  const safeValue = Math.max(0, Math.min(100, Number(value) || 0))
  return (
    <div className="metric">
      <div className="metric-head">
        <span>{label}</span>
        <strong>{safeValue}%</strong>
      </div>
      <div className="metric-track">
        <div className="metric-fill" style={{ width: `${safeValue}%`, background: color }} />
      </div>
    </div>
  )
}

function Badge({ tone = 'neutral', children }) {
  return <span className={`badge ${tone}`}>{children}</span>
}

function ResultCard({ tabKey, result }) {
  if (!result) {
    return null
  }

  if (tabKey === 'deepfake') {
    const verdict = result.verdict || 'UNCERTAIN'
    const risk = result.risk_level || 'MEDIUM'
    const tone = verdict === 'REAL' ? 'good' : verdict === 'UNCERTAIN' ? 'warn' : 'danger'

    return (
      <div className="result-card">
        <div className="result-head">
          <Badge tone={tone}>{verdict.replaceAll('_', ' ')}</Badge>
          <Badge>{risk} RISK</Badge>
        </div>
        <ProgressBar label="Detection Confidence" value={result.confidence} color="#8b5cf6" />
        <ProgressBar label="Manipulation Likelihood" value={riskToPercent[risk] ?? 50} color="#ef4444" />
        {result.summary && <p className="summary">{result.summary}</p>}
        {Array.isArray(result.indicators) && result.indicators.length > 0 && (
          <ul className="list">
            {result.indicators.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  if (tabKey === 'handwriting') {
    const verdict = result.verdict || 'UNCERTAIN'
    const aiProb = result.is_ai_origin ? result.confidence : 100 - (result.confidence ?? 50)
    const humanProb = 100 - aiProb
    const tone =
      verdict === 'HUMAN_HANDWRITTEN'
        ? 'good'
        : verdict === 'AI_SIMULATED_HANDWRITING' || verdict === 'AI_GENERATED_TEXT'
          ? 'danger'
          : 'warn'

    return (
      <div className="result-card">
        <div className="result-head">
          <Badge tone={tone}>{verdict.replaceAll('_', ' ')}</Badge>
          <Badge>{result.is_ai_origin ? 'AI ORIGIN' : 'HUMAN ORIGIN'}</Badge>
        </div>
        <ProgressBar label="AI Origin Probability" value={aiProb} color="#f43f5e" />
        <ProgressBar label="Human Origin Probability" value={humanProb} color="#22c55e" />
        <ProgressBar label="Legibility" value={result.legibility_score} color="#38bdf8" />
        {result.summary && <p className="summary">{result.summary}</p>}
        {Array.isArray(result.indicators) && result.indicators.length > 0 && (
          <ul className="list">
            {result.indicators.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  if (tabKey === 'fake-news') {
    const verdict = result.verdict || 'UNVERIFIED'
    const tone = verdict === 'TRUE' ? 'good' : verdict === 'FALSE' ? 'danger' : 'warn'

    return (
      <div className="result-card">
        <div className="result-head">
          <Badge tone={tone}>{verdict.replaceAll('_', ' ')}</Badge>
          <Badge>CLAIM CHECK</Badge>
        </div>
        <ProgressBar label="Fact-check Confidence" value={result.confidence} color="#a78bfa" />
        <ProgressBar label="Credibility Score" value={result.credibility_score} color="#60a5fa" />
        {result.extracted_claim && <p className="claim">Detected claim: {result.extracted_claim}</p>}
        {result.summary && <p className="summary">{result.summary}</p>}
        {Array.isArray(result.key_findings) && result.key_findings.length > 0 && (
          <ul className="list">
            {result.key_findings.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  return null
}

function App() {
  const [activeTab, setActiveTab] = useState('deepfake')
  const [files, setFiles] = useState({})
  const [results, setResults] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const activeConfig = useMemo(() => TABS.find((tab) => tab.key === activeTab), [activeTab])
  const activeFile = files[activeTab]
  const activeResult = results[activeTab]
  const [previewUrl, setPreviewUrl] = useState('')

  useEffect(() => {
    if (!activeFile) {
      setPreviewUrl('')
      return
    }

    const nextPreview = URL.createObjectURL(activeFile)
    setPreviewUrl(nextPreview)

    return () => {
      URL.revokeObjectURL(nextPreview)
    }
  }, [activeFile])

  const onFileChange = (event) => {
    const selected = event.target.files?.[0]
    setFiles((prev) => ({ ...prev, [activeTab]: selected }))
    setResults((prev) => ({ ...prev, [activeTab]: null }))
    setError('')
  }

  const onAnalyze = async () => {
    if (!activeFile || !activeConfig) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const body = new FormData()
      body.append('image', activeFile)

      const response = await fetch(`${API_BASE}${activeConfig.endpoint}`, {
        method: 'POST',
        body
      })

      if (!response.ok) {
        const failed = await response.json().catch(() => ({}))
        throw new Error(failed.detail || `Request failed with status ${response.status}`)
      }

      const data = await response.json()
      setResults((prev) => ({ ...prev, [activeTab]: data }))
    } catch (requestError) {
      setError(requestError.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <section className="hero">
        <p className="eyebrow">AI Detection Suite</p>
        <h1>AI Detection Hub</h1>
        <p className="subtitle">Deepfake analysis, handwriting authenticity checks, and fake news verification in one immersive workflow.</p>
      </section>

      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={tab.key === activeTab ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            <span>{tab.emoji}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <section className="panel">
        <div className="panel-grid">
          <div className="upload-zone">
            <h2>{activeConfig?.emoji} {activeConfig?.label}</h2>
            <p className="helper">{activeConfig?.helper}</p>
            <label className="file-label" htmlFor="image-upload">Upload image</label>
            <input id="image-upload" type="file" accept="image/*" onChange={onFileChange} />
            {activeFile && <p className="file-meta">{activeFile.name} · {(activeFile.size / 1024).toFixed(1)} KB</p>}
            <button type="button" className="analyze" onClick={onAnalyze} disabled={!activeFile || loading}>
              {loading ? 'Analyzing…' : activeConfig?.button}
            </button>
            {error && <p className="error">{error}</p>}
          </div>

          <div className="preview-zone">
            {previewUrl ? (
              <img src={previewUrl} alt="Uploaded preview" className="preview" />
            ) : (
              <div className="preview-empty">Upload an image to preview and analyze.</div>
            )}
          </div>
        </div>

        {activeResult && (
          <div className="result">
            <h3>Analysis Result</h3>
            <ResultCard tabKey={activeTab} result={activeResult} />
            <details>
              <summary>Raw JSON</summary>
              <pre>{JSON.stringify(activeResult, null, 2)}</pre>
            </details>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
