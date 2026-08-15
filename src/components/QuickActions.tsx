import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from './ToastProvider'

const QuickActions: React.FC = ()=>{
  const navigate = useNavigate()
  const { addToast } = useToast()
  return (
    <div className="card">
      <h3>Quick actions</h3>
      <div style={{display:'flex',flexWrap:'wrap',gap:8,marginTop:8}}>
        <button className="button" onClick={()=>navigate('/properties')}>Properties</button>
        <button className="button" onClick={()=>navigate('/properties')}>Add Property</button>
        <button className="button muted" onClick={()=>addToast({ message: 'Units UI requires backend endpoints', type: 'info' })}>Add Unit</button>
        <button className="button muted" onClick={()=>addToast({ message: 'Tenants UI requires backend endpoints', type: 'info' })}>Add Tenant</button>
        <button className="button muted" onClick={()=>addToast({ message: 'Create Lease requires backend endpoints', type: 'info' })}>Create Lease</button>
      </div>
    </div>
  )
}

export default QuickActions
