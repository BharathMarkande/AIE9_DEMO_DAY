import React, { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'

const phrases = [
  'Detect emotional bias',
  'Identify loss escalation',
  'Control risk',
  'Trade with discipline',
]

export function OscillatingHeadline({ items = phrases, intervalMs = 3000 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (!items || items.length === 0) return

    const id = setInterval(() => {
      setIndex((prev) => (prev + 1) % items.length)
    }, intervalMs)

    return () => clearInterval(id)
  }, [items, intervalMs])

  return (
    <div className="oscillating-headline-wrapper" aria-live="polite">
      <AnimatePresence mode="wait">
        <motion.span
          key={items[index]}
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -28 }}
          transition={{ duration: 0.6, ease: [0.22, 0.61, 0.36, 1] }}
          className="oscillating-headline-text block mb-2 text-white"
        >
          {items[index]}
        </motion.span>
      </AnimatePresence>
    </div>
  )
}

export function OscillatingHeadlineSection() {
  return (
    <section className="oscillating-hero-section">
      <div className="oscillating-hero-inner glass-card">
        <OscillatingHeadline />
      </div>
    </section>
  )
}

