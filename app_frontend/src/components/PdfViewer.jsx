import { useEffect, useRef, useState } from 'react'
// Use legacy build path for bundler compatibility
import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs'
import workerSrc from 'pdfjs-dist/legacy/build/pdf.worker.mjs?worker&url'

GlobalWorkerOptions.workerSrc = workerSrc

export default function PdfViewer({ fileUrl, target }) {
  const containerRef = useRef(null)
  const [doc, setDoc] = useState(null)
  const [numPages, setNumPages] = useState(0)
  const [renderedPages, setRenderedPages] = useState({})

  useEffect(() => {
    let cancelled = false
    if (!fileUrl) { setDoc(null); setNumPages(0); setRenderedPages({}); return }
    ;(async () => {
      try {
        const loadingTask = getDocument({ url: fileUrl, withCredentials: false })
        const loaded = await loadingTask.promise
        if (cancelled) return
        setDoc(loaded)
        setNumPages(loaded.numPages)
        setRenderedPages({})
      } catch (e) {
        console.error('PDF load failed', e)
        setDoc(null)
        setNumPages(0)
      }
    })()
    return () => { cancelled = true }
  }, [fileUrl])

  useEffect(() => {
    if (!doc || !numPages) return
    const container = containerRef.current
    if (!container) return

    // Clear previous canvases
    container.innerHTML = ''

    const scale = 1.5
    const pageDivs = []
    let cancelled = false

    const renderPage = async (pageNumber) => {
      try {
        const page = await doc.getPage(pageNumber)
        if (cancelled) return
        const viewport = page.getViewport({ scale })
        const pageDiv = document.createElement('div')
        pageDiv.style.position = 'relative'
        pageDiv.style.margin = '8px auto'
        pageDiv.style.width = `${viewport.width}px`
        pageDiv.style.height = `${viewport.height}px`
        const canvas = document.createElement('canvas')
        canvas.width = viewport.width
        canvas.height = viewport.height
        canvas.style.width = `${viewport.width}px`
        canvas.style.height = `${viewport.height}px`
        const ctx = canvas.getContext('2d')
        pageDiv.appendChild(canvas)
        container.appendChild(pageDiv)
        pageDivs[pageNumber] = pageDiv
        const renderTask = page.render({ canvasContext: ctx, viewport })
        await renderTask.promise

        // If target is for this page, draw overlay and scroll
        if (target && target.page === (pageNumber - 1) && Array.isArray(target.bbox)) {
          const [x0, y0, x1, y1] = target.bbox
          const rx = x0 * scale
          const ry = y0 * scale
          const rw = (x1 - x0) * scale
          const rh = (y1 - y0) * scale
          const overlay = document.createElement('div')
          overlay.style.position = 'absolute'
          overlay.style.left = `${rx}px`
          overlay.style.top = `${ry}px`
          overlay.style.width = `${rw}px`
          overlay.style.height = `${rh}px`
          overlay.style.background = 'rgba(255, 217, 51, 0.25)'
          overlay.style.border = '2px solid rgba(255, 217, 51, 0.9)'
          pageDiv.appendChild(overlay)

          // Scroll so the center of the rect is visible
          const targetY = pageDiv.offsetTop + ry + rh / 2 - container.clientHeight / 2
          container.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' })
        }
      } catch (e) { /* ignore per-page errors */ }
    }

    // Render all pages sequentially (simple but OK for demo)
    ;(async () => {
      for (let p = 1; p <= numPages; p++) {
        if (cancelled) break
        await renderPage(p)
      }
    })()

    return () => { cancelled = true }
  }, [doc, numPages, target])

  return (
    <div ref={containerRef} style={{ overflow: 'auto', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#0a0f1e' }} />
  )
}
