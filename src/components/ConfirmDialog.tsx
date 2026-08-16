import React from 'react'

type Props = {
  open: boolean
  title?: string
  description?: string
  onConfirm: ()=>void
  onCancel: ()=>void
  children?: React.ReactNode
}

const ConfirmDialog: React.FC<Props> = ({ open, title='Confirm', description, onConfirm, onCancel, children }) => {
  if(!open) return null
  return (
    <div className="modal-overlay">
      <div className="modal card">
        <h3>{title}</h3>
        {description && <p>{description}</p>}
        {children}
        <div style={{display:'flex',gap:8,marginTop:12}}>
          <button className="button danger" onClick={onConfirm}>Confirm</button>
          <button className="button muted" onClick={onCancel}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmDialog
