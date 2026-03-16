import React, { useState, useEffect, useRef } from 'react'
import { uploadSession } from '../services/api'

const RISK_STORAGE_KEY = 'riskhalo_risk_per_trade'
const MIN_RR_STORAGE_KEY = 'riskhalo_min_rr'
const MAX_TRADES_STORAGE_KEY = 'riskhalo_max_trades_per_day'
const MAX_DAILY_LOSS_STORAGE_KEY = 'riskhalo_max_daily_loss'

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
  const [minRR, setMinRR] = useState(() => {
    try {
      const saved = localStorage.getItem(MIN_RR_STORAGE_KEY)
      return saved !== null ? Number(saved) : 1.5
    } catch {
      return 1.5
    }
  })
  const [maxTradesPerDay, setMaxTradesPerDay] = useState(() => {
    try {
      const saved = localStorage.getItem(MAX_TRADES_STORAGE_KEY)
      return saved !== null ? Number(saved) : 3
    } catch {
      return 3
    }
  })
  const [maxDailyLoss, setMaxDailyLoss] = useState(() => {
    try {
      const saved = localStorage.getItem(MAX_DAILY_LOSS_STORAGE_KEY)
      return saved !== null ? Number(saved) : 5000
    } catch {
      return 5000
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

  useEffect(() => {
    try {
      localStorage.setItem(MIN_RR_STORAGE_KEY, String(minRR))
    } catch (_) {}
  }, [minRR])

  useEffect(() => {
    try {
      localStorage.setItem(MAX_TRADES_STORAGE_KEY, String(maxTradesPerDay))
    } catch (_) {}
  }, [maxTradesPerDay])

  useEffect(() => {
    try {
      localStorage.setItem(MAX_DAILY_LOSS_STORAGE_KEY, String(maxDailyLoss))
    } catch (_) {}
  }, [maxDailyLoss])

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
    if (minRR <= 0 || isNaN(minRR)) {
      setMessage('Please enter a valid minimum R:R')
      setIsError(true)
      return
    }
    if (maxTradesPerDay <= 0 || isNaN(maxTradesPerDay)) {
      setMessage('Please enter a valid max trades per day')
      setIsError(true)
      return
    }
    if (maxDailyLoss <= 0 || isNaN(maxDailyLoss)) {
      setMessage('Please enter a valid max daily loss')
      setIsError(true)
      return
    }
    setLoading(true)
    setMessage(null)
    setIsError(false)
    try {
      const result = await uploadSession(
        file,
        riskPerTrade,
        minRR,
        maxTradesPerDay,
        maxDailyLoss
      )
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
          <label className="label">Risk per Trade (₹)</label>
          <input
            type="number"
            min={1}
            value={riskPerTrade}
            onChange={(e) => setRiskPerTrade(Number(e.target.value) || 0)}
            className="input-number"
            disabled={loading}
          />
        </div>
        <div className="form-row">
          <label className="label">Minimum Risk:Reward (R:R)</label>
          <input
            type="number"
            min={0.1}
            step={0.1}
            value={minRR}
            onChange={(e) => setMinRR(Number(e.target.value) || 0)}
            className="input-number"
            disabled={loading}
          />
        </div>
        <div className="form-row">
          <label className="label">Max Trades per Day</label>
          <input
            type="number"
            min={1}
            value={maxTradesPerDay}
            onChange={(e) => setMaxTradesPerDay(Number(e.target.value) || 0)}
            className="input-number"
            disabled={loading}
          />
        </div>
        <div className="form-row">
          <label className="label">Max Daily Loss (₹)</label>
          <input
            type="number"
            min={1}
            value={maxDailyLoss}
            onChange={(e) => setMaxDailyLoss(Number(e.target.value) || 0)}
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
