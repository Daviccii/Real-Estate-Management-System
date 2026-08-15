import React, { createContext, useContext, useState, useCallback } from 'react'

type Toast = { id: string, message: string, type?: 'info'|'success'|'error' }

const ToastContext = createContext<{ addToast:(t: Omit<Toast,'id'>)=>string, removeToast:(id:string)=>void } | undefined>(undefined)

export const ToastProvider: React.FC<{children:React.ReactNode}> = ({ children }) => {
  const [toasts,setToasts] = useState<Toast[]>([])

  const addToast = useCallback((t: Omit<Toast,'id'>)=>{
    const id = String(Date.now())
    setToasts(s=>[...s, { id, ...t }])
    setTimeout(()=> setToasts(s=>s.filter(x=>x.id!==id)), 4000)
    return id
  },[])

  const removeToast = useCallback((id:string)=>{
    setToasts(s=>s.filter(t=>t.id!==id))
  },[])

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div aria-live="polite" className="toast-viewport">
        {toasts.map(t=> (
          <div key={t.id} className={`toast ${t.type||'info'}`} role="status">
            {t.message}
            <button aria-label="Dismiss" onClick={()=>removeToast(t.id)} className="toast-close">×</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(){
  const ctx = useContext(ToastContext)
  if(!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}

export default ToastProvider
