import React from 'react'
import { Outlet } from 'react-router-dom'
import PublicNavbar from '../components/PublicNavbar'
import PublicFooter from '../components/PublicFooter'

const PublicLayout: React.FC = ()=>{
  return (
    <div className="public-page">
      <PublicNavbar />
      <main style={{minHeight:'60vh'}} className="public-content">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  )
}

export default PublicLayout
