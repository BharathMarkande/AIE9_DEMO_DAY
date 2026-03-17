import React, { useState } from 'react'
import Header from './components/Header'
import UploadPanel from './components/UploadPanel'
import SessionSummaryCard from './components/SessionSummaryCard'
import ChatWindow from './components/ChatWindow'
import { OscillatingHeadlineSection } from './components/OscillatingHeadline'

export default function App() {
  const [sessionAnalysis, setSessionAnalysis] = useState(null)

  const handleUploadSuccess = (result) => {
    if (result && (result.behavioral_state != null || result.narrative_summary != null)) {
      setSessionAnalysis({
        behavioral_state: result.behavioral_state,
        severity_score: result.severity_score,
        expectancy_summary: result.expectancy_summary,
        discipline_score: result.discipline_score,
        narrative_summary: result.narrative_summary,
        rule_narrative: result.rule_narrative,
      })
    }
  }

  return (
    <div className="app">
      <div className="app-backdrop" aria-hidden />
      <Header />
      <main className="main">
        <OscillatingHeadlineSection />
        <div className="main-panels">
          <UploadPanel onUploadSuccess={handleUploadSuccess} />
          {sessionAnalysis && (
            <SessionSummaryCard
              analysis={sessionAnalysis}
              onDismiss={() => setSessionAnalysis(null)}
            />
          )}
          {!sessionAnalysis && (
            <section className="glass-card session-summary-card session-summary-card--empty">
              <h2 className="panel-title session-summary-title">Trading Session Analysis</h2>
              <p className="session-summary-empty-copy">
                Upload a weekly trade journal on the left to see your behavioral risk profile.
              </p>
            </section>
          )}
          <ChatWindow />
        </div>
        <footer className="app-footer">
          <p className="app-footer-text">
          AIE09 Certification Challenge - RiskHalo prototype - By BHARATH MARKANDE
          </p>
        </footer>
      </main>
    </div>
  )
}
