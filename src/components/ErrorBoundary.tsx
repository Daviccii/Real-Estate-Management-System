import React from 'react'

type State = { hasError: boolean, error?: any }

class ErrorBoundary extends React.Component<{children:React.ReactNode}, State> {
  constructor(props:any){ super(props); this.state = { hasError:false } }
  static getDerivedStateFromError(error:any){ return { hasError:true, error } }
  componentDidCatch(error:any, info:any){ console.error('Uncaught error:', error, info) }
  render(){
    if(this.state.hasError){
      return (
        <div style={{padding:24}}>
          <h2>Something went wrong</h2>
          <pre style={{whiteSpace:'pre-wrap',color:'var(--danger)'}}>{String(this.state.error)}</pre>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary
