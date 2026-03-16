import React, { useState } from 'react'

const BEHAVIORAL_ITEMS = [
  { label: 'STABLE', desc: 'Your performance stays consistent regardless of recent losses.' },
  { label: 'LOSS_ESCALATION', desc: 'Your losses become larger after losing trades (emotional risk escalation or revenge trading).' },
  { label: 'CONFIDENCE_CONTRACTION', desc: 'Your winning trades shrink after losses (hesitation or reduced conviction).' },
  { label: 'ADAPTIVE_RECOVERY', desc: 'Your performance improves after losses, showing resilience.' },
]

const METRIC_INFO = {
  behavioral_state: {
    title: 'Behavioral State',
    intro: 'How you trade after a losing trade compared to normal conditions:',
    items: BEHAVIORAL_ITEMS,
  },
  severity: {
    title: 'Severity Level',
    body: 'This measures how strongly your performance changes after losses — closer to 0 means stable, closer to 1 means highly distorted. Displayed on a 1–5 scale.',
  },
  expectancy: {
    title: 'Expectancy Impact',
    body: 'Expectancy is the average outcome per trade in "R" (your risk per trade). Normal = expectancy in neutral conditions; Post-loss = after a loss. Delta (Δ) is the change; negative means performance worsens after losses. The rupee impact estimates how much that shift cost over this period.',
  },
  discipline: {
    title: 'Discipline Score',
    body: 'A 0-100 score for how well you followed your rules: risk per trade, daily loss limits, overtrading limits, and minimum risk:reward on winners. Higher is better.',
  },
}

function InfoTooltip({ id, metricKey, variant }) {
  const info = METRIC_INFO[metricKey]
  if (!info) return null
  const isBehavioral = metricKey === 'behavioral_state'
  return (
    <span className="session-summary-info-wrap">
      <button
        type="button"
        className={`session-summary-info-icon ${variant ? `session-summary-info-icon--${variant}` : ''}`}
        aria-label={`Information: ${info.title}`}
        aria-describedby={id}
      >
        ?
      </button>
      <span
        id={id}
        className={`session-summary-info-tooltip ${isBehavioral ? 'session-summary-info-tooltip--behavioral' : ''}`}
        role="tooltip"
      >
        <strong>{info.title}</strong>
        {isBehavioral ? (
          <div className="session-summary-tooltip-body">
            <p className="session-summary-tooltip-intro">{info.intro}</p>
            {info.items.map((item, i) => (
              <div key={i} className="session-summary-tooltip-item">
                <strong>{i + 1}. {item.label}</strong> — {item.desc}
              </div>
            ))}
          </div>
        ) : (
          <span>{info.body}</span>
        )}
      </span>
    </span>
  )
}

/**
 * Session Analysis Card: shows behavioral state, severity, expectancy impact,
 * discipline score, and an expandable "View Full Analysis" with the full narrative.
 */
export default function SessionSummaryCard({ analysis, onDismiss }) {
  const [expanded, setExpanded] = useState(false)

  if (!analysis) return null

  const {
    behavioral_state,
    severity_score,
    expectancy_summary,
    discipline_score,
    narrative_summary,
    rule_narrative,
  } = analysis

  const formatExpectancy = () => {
    if (!expectancy_summary) return '—'
    const { expectancy_normal_R, expectancy_post_R, expectancy_delta_R, economic_impact_rupees } = expectancy_summary
    if ([expectancy_normal_R, expectancy_post_R, expectancy_delta_R, economic_impact_rupees].every((v) => v == null)) {
      return '—'
    }
    const parts = []
    if (expectancy_normal_R != null) parts.push(`Normal: ${expectancy_normal_R}R`)
    if (expectancy_post_R != null) parts.push(`Post-loss: ${expectancy_post_R}R`)
    if (expectancy_delta_R != null) parts.push(`Δ ${expectancy_delta_R}R`)
    if (economic_impact_rupees != null) parts.push(`≈ ₹${Math.round(economic_impact_rupees)} impact`)
    return parts.join(' · ')
  }

  // Map severity 0–1 to 1–5 scale for display
  const severityLevel = severity_score != null
    ? Math.min(5, Math.max(1, Math.round(severity_score * 5)))
    : null

  // Format behavioral state for display (e.g. LOSS_ESCALATION → LOSS / ESCALATION)
  const formatBehavioralState = (state) => {
    if (!state) return { primary: '—', secondary: '' }
    const parts = String(state).split('_')
    if (parts.length >= 2) {
      return { primary: parts[0], secondary: parts.slice(1).join(' ') }
    }
    return { primary: state, secondary: '' }
  }
  const behavioralDisplay = formatBehavioralState(behavioral_state)
  const isPositiveBehavioral = ['STABLE', 'ADAPTIVE_RECOVERY'].includes(String(behavioral_state || '').toUpperCase())

  // Emojis for each metric
  const BEHAVIORAL_EMOJI = '🧠'
  const SEVERITY_EMOJI = '⚠️'
  const DISCIPLINE_EMOJI = '🎯'

  return (
    <section className="glass-card session-summary-card" aria-label="Session analysis">
      <div className="session-summary-header">
        <h2 className="panel-title session-summary-title">trading Session Analysis</h2>
        {onDismiss && (
          <button
            type="button"
            className="session-summary-dismiss"
            onClick={onDismiss}
            aria-label="Dismiss analysis"
          >
            ×
          </button>
        )}
      </div>

      <div className="session-summary-grid">
        <div className={`session-summary-card-item session-summary-card-behavioral ${isPositiveBehavioral ? 'session-summary-card-positive' : ''}`}>
          <div className="session-summary-card-header">
            <span className="session-summary-card-title">BEHAVIORAL STATE</span>
            <InfoTooltip id="info-behavioral-state" metricKey="behavioral_state" variant="red" />
          </div>
          <div className="session-summary-card-body">
            <span className="session-summary-card-emoji" aria-hidden>{BEHAVIORAL_EMOJI}</span>
            <div className="session-summary-card-value-wrap">
              <span className="session-summary-card-value session-summary-state-value">
                {behavioralDisplay.primary}
              </span>
              {behavioralDisplay.secondary && (
                <span className="session-summary-card-value-secondary">{behavioralDisplay.secondary}</span>
              )}
            </div>
          </div>
        </div>

        <div className="session-summary-card-item session-summary-card-severity">
          <div className="session-summary-card-header">
            <span className="session-summary-card-title">SEVERITY LEVEL</span>
            <InfoTooltip id="info-severity" metricKey="severity" variant="yellow" />
          </div>
          <div className="session-summary-card-body session-summary-card-body-severity">
            <span className="session-summary-card-emoji" aria-hidden>{SEVERITY_EMOJI}</span>
            <div className="session-summary-card-value-wrap">
              <span className="session-summary-card-value session-summary-severity-value">
                {severityLevel != null ? `${severityLevel}/5` : '—'}
              </span>
              {severityLevel != null && (
                <div className="session-summary-severity-bar" role="meter" aria-valuenow={severityLevel} aria-valuemin={1} aria-valuemax={5}>
                  {[1, 2, 3, 4, 5].map((i) => (
                    <span
                      key={i}
                      className={`session-summary-severity-segment ${i <= severityLevel ? 'active' : ''}`}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="session-summary-card-item session-summary-card-discipline">
          <div className="session-summary-card-header">
            <span className="session-summary-card-title">DISCIPLINE SCORE</span>
            <InfoTooltip id="info-discipline" metricKey="discipline" variant="cyan" />
          </div>
          <div className="session-summary-card-body">
            <span className="session-summary-card-emoji" aria-hidden>{DISCIPLINE_EMOJI}</span>
            <span className="session-summary-card-value session-summary-discipline-value">
              {discipline_score != null ? `${discipline_score}/100` : '—'}
            </span>
          </div>
        </div>
      </div>

      <div className="session-summary-expand">
        <button
          type="button"
          className="session-summary-expand-btn"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
        >
          {expanded ? 'Hide Full Analysis' : 'View Full Analysis'}
          <span className="session-summary-expand-icon" aria-hidden>{expanded ? ' ▲' : ' ▼'}</span>
        </button>
        {expanded && (
          <div className="session-summary-narrative-wrap">
            {narrative_summary && (
              <div className="session-summary-narrative-block">
                <h3 className="session-summary-narrative-heading">Behavioral & performance</h3>
                <div className="session-summary-narrative">{narrative_summary}</div>
              </div>
            )}
            {rule_narrative && (
              <div className="session-summary-narrative-block">
                <h3 className="session-summary-narrative-heading">Rule compliance</h3>
                <div className="session-summary-narrative">{rule_narrative}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
