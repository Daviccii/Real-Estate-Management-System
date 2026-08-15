import React from 'react'

export default function About(){
  return (
    <div className="page">
      <h1>Building a smarter future for real estate management.</h1>
      <p style={{color:'var(--muted)'}}>
        PropNoxa is designed to bring property operations into one connected platform — from listing and leasing to maintenance and financials.
      </p>

      <section style={{marginTop:20}}>
        <h3>Our Mission</h3>
        <p className="muted">Help property teams operate efficiently with modern software and reliable data.</p>
      </section>

      <section style={{marginTop:12}}>
        <h3>Our Vision</h3>
        <p className="muted">A unified operating system that makes property management predictable and profitable.</p>
      </section>
    </div>
  )
}
