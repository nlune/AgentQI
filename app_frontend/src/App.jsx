import { useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'
import './App.css'

function useApiBase() {
  const defaultBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
  const [apiBase, setApiBase] = useState(() => localStorage.getItem('apiBase') || defaultBase)
  useEffect(() => { localStorage.setItem('apiBase', apiBase) }, [apiBase])
  const originBase = useMemo(() => apiBase.replace(/\/$/, '').replace(/\/api\/v1$/, ''), [apiBase])
  return { apiBase, setApiBase, originBase }
}

function App() {
  const { apiBase, setApiBase, originBase } = useApiBase()
  const [docName, setDocName] = useState(null)
  const [pdfUrl, setPdfUrl] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [queryText, setQueryText] = useState('What type of certificate is this?')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState([]) // {role:'user'|'assistant', text}
  const fileRef = useRef()

  const haveDoc = !!docName

  async function uploadPDF() {
    const file = fileRef.current?.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file, file.name)
      // Let axios set the multipart boundary header automatically
      const { data } = await axios.post(`${apiBase}/process-pdf`, fd)
      const name = data.document_name || data.filename || file.name
      setDocName(name)
      setPdfUrl(`${originBase}/pdfs/original/${encodeURIComponent(name)}`)
    } catch (e) {
      console.error(e)
      alert(e?.response?.data?.detail || e.message)
    } finally {
      setUploading(false)
    }
  }

  async function sendQuery() {
    if (!docName) { alert('Upload a PDF first.'); return }
    const q = queryText.trim()
    if (!q) return
    setSending(true)
    setMessages((m) => [...m, { role: 'user', text: q }])
    try {
      const { data } = await axios.post(`${apiBase}/query`, null, { params: { query: q, doc_name: docName, k: 5 } })
      const answer = data.result || '(no result)'
      setMessages((m) => [...m, { role: 'assistant', text: answer }])
      const ev = data.evidence || {}
      const chunkIds = (ev.chunk_id || []).map((x) => parseInt(x, 10)).filter((n) => Number.isFinite(n))
      if (chunkIds.length) {
        await highlightChunks(docName, chunkIds.slice(0, 5))
      }
    } catch (e) {
      console.error(e)
      setMessages((m) => [...m, { role: 'assistant', text: `Error: ${e?.response?.data?.detail || e.message}` }])
    } finally {
      setSending(false)
    }
  }

  async function highlightChunks(docName, chunkIds) {
    try {
      const payload = { doc_name: docName, chunk_ids: chunkIds, color: [1, 0.85, 0.2], return_pdf: false }
      const { data } = await axios.post(`${apiBase}/highlight`, payload)
      if (data.annotated_pdf_url) {
        setPdfUrl(`${originBase}${data.annotated_pdf_url}`)
      }
    } catch (e) {
      console.warn('Highlight error', e)
    }
  }

  return (
    <div className="app">
      <div className="header">
        <h1>AgentQI PDF QA</h1>
        <div className="api">
          <small>API base</small>
          <input type="text" value={apiBase} onChange={(e) => setApiBase(e.target.value)} placeholder="http://localhost:8000/api/v1" />
        </div>
      </div>
      <div className="main">
        <div className="left">
          <div className="toolbar">
            <input ref={fileRef} type="file" accept="application/pdf" />
            <button onClick={uploadPDF} disabled={uploading}>{uploading ? 'Uploading…' : 'Upload & Process'}</button>
            {haveDoc && <span className="meta" title={docName}>{docName}</span>}
          </div>
          <div className="viewer">
            {pdfUrl ? (
              <iframe title="PDF Viewer" src={pdfUrl} />
            ) : (
              <div style={{ padding: 16, color: '#9ca3af' }}>Upload a PDF to view it here.</div>
            )}
          </div>
          <div className="links">
            {docName && <>
              <span>Original:</span>
              <a href={`${originBase}/pdfs/original/${encodeURIComponent(docName)}`} target="_blank" rel="noreferrer">open</a>
              <span>Annotated:</span>
              <a href={`${originBase}/pdfs/annotated/${encodeURIComponent(docName)}__annotated.pdf`} target="_blank" rel="noreferrer">open</a>
            </>}
          </div>
        </div>
        <div className="right">
          <div className="chat">
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`msg ${m.role}`}>
                  <div className="title">{m.role === 'user' ? 'You' : 'Assistant'}</div>
                  <div>{m.text}</div>
                </div>
              ))}
            </div>
            <div className="composer">
              <textarea value={queryText} onChange={(e) => setQueryText(e.target.value)} placeholder="Ask a question about the PDF…" />
              <button onClick={sendQuery} disabled={!docName || sending}>{sending ? 'Sending…' : 'Send'}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
