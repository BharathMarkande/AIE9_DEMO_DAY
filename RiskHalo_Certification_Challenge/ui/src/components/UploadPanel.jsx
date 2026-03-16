import React, { useState, useEffect, useRef } from 'react'
import { uploadSession } from '../services/api'

const RISK_STORAGE_KEY = 'riskhalo_risk_per_trade'

export default function UploadPanel({ onUploadSuccess, onUploadError }) {
  const [file, setFile] = useState(null)
  const [riskPerTrade, setRiskPerTrade] = useState(() => {
    try {
      const saved = localStorage.getItem(RISK_STORAGE_KEY)
      return saved !== null ? Number(saved) : 2000
    } catch {
      return 2000
    }
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [isError, setIsError] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    try {
      localStorage.setItem(RISK_STORAGE_KEY, String(riskPerTrade))
    } catch (_) {}
  }, [riskPerTrade])

  const handleFileChange = (e) => {
    const f = e.target.files?.[0]
    setFile(f || null)
    setMessage(null)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    const f = e.dataTransfer?.files?.[0]
    if (f && (f.name.endsWith('.xlsx') || f.name.endsWith('.xls'))) {
      setFile(f)
      setMessage(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setMessage('Please select a weekly trade file (.xlsx)')
      setIsError(true)
      return
    }
    if (riskPerTrade <= 0 || isNaN(riskPerTrade)) {
      setMessage('Please enter a valid risk per trade')
      setIsError(true)
      return
    }
    setLoading(true)
    setMessage(null)
    setIsError(false)
    try {
      const result = await uploadSession(file, riskPerTrade)
      setMessage(result.message || 'Session analyzed successfully.')
      setIsError(false)
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      onUploadSuccess?.(result)
      // Result may include: behavioral_state, severity_score, expectancy_summary, discipline_score, narrative_summary
    } catch (err) {
      const msg = err.message || 'Upload failed'
      setMessage(msg)
      setIsError(true)
      onUploadError?.(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="glass-card upload-panel">
      <h2 className="panel-title upload-panel-title">Upload Trading Session</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <div
          className={`upload-dropzone ${isDragging ? 'upload-dropzone--active' : ''} ${file ? 'upload-dropzone--has-file' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
            className="upload-dropzone-input"
            disabled={loading}
          />
          <span className="upload-dropzone-icon">📄</span>
          <span className="upload-dropzone-text">
            {file ? file.name : 'Drag & Drop Trade Journal (.xlsx)'}
          </span>
        </div>
        <div className="form-row">
          <label className="label">Risk per Trade</label>
          <input
            type="number"
            min={1}
            value={riskPerTrade}
            onChange={(e) => setRiskPerTrade(Number(e.target.value) || 0)}
            className="input-number"
            disabled={loading}
          />
        </div>
        <button type="submit" className="btn-primary btn-behavioral" disabled={loading}>
          {loading ? (
            <>
              <span className="spinner" aria-hidden />
              Analyzing...
            </>
          ) : (
            'Run Behavioral Risk Analysis'
          )}
        </button>
      </form>
      {message && (
        <p className={`upload-message ${isError ? 'error' : 'success'}`}>
          {message}
        </p>
      )}
    </section>
  )
}
