import React from 'react'

export default function Header() {
  return (
    <header className="header">
      <div className="header-left">
        <img
          src="/logo.png"
          alt="RiskHalo logo"
          className="header-logo"
        />
        <div className="header-text">
          <h1 className="header-title riskhalo-logo">
            <span>RISK</span>
            <span className="header-hal">HAL</span>
            <span>O</span>
          </h1>
          <p className="header-subtitle">Behavioral Intelligence for Traders</p>
        </div>
      </div>
    </header>
  )
}
