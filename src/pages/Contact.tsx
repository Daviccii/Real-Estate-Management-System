import React, {useState} from 'react'

export default function Contact(){
  const [loading,setLoading]=useState(false)
  const [sent,setSent]=useState(false)
  const [err,setErr]=useState<string | null>(null)

  const handleSubmit = async (e:React.FormEvent) =>{
    e.preventDefault()
    setErr(null)
    setLoading(true)
    // No backend endpoint — show clear message
    setTimeout(()=>{
      setLoading(false)
      setErr('No contact endpoint configured. Please reach out via email: support@propnoxa.example')
    },800)
  }

  if(sent) return <div className="card">Message sent — we'll be in touch.</div>

  return (
    <div className="page">
      <h1>Let's talk about your property.</h1>
      <form onSubmit={handleSubmit} className="card" style={{maxWidth:720,display:'grid',gap:12}}>
        <input className="input" placeholder="Name" required />
        <input className="input" placeholder="Email" type="email" required />
        <input className="input" placeholder="Phone" />
        <input className="input" placeholder="Company" />
        <input className="input" placeholder="Subject" />
        <textarea className="input" placeholder="Message" rows={6} />
        {err && <div style={{color:'var(--danger)'}}>{err}</div>}
        <div style={{display:'flex',gap:8}}>
          <button className="button" type="submit" disabled={loading}>{loading? 'Sending...':'Send Message'}</button>
        </div>
      </form>
    </div>
  )
}
