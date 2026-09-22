import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/auth'
import type { User, UserRole } from '../types'

type AuthContextType = {
  user: User | null
  loading: boolean
  login: (email:string,password:string)=>Promise<void>
  register: (email:string,password:string,full_name?:string)=>Promise<void>
  logout: ()=>void
  hasRole: (role: UserRole) => boolean
  hasAnyRole: (roles: UserRole[]) => boolean
  getDashboardPath: () => string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{children:React.ReactNode}> = ({children}) =>{
  const [user,setUser] = useState<User | null>(null)
  const [loading,setLoading] = useState(true)

  useEffect(()=>{
    let mounted=true
    // Only attempt to refresh when on protected routes to avoid
    // triggering 401s for public visitors (refresh relies on httponly cookie).
    try{
      const path = window?.location?.pathname || ''
      // Check if this is a protected route (app, admin, agent, manager, tenant, owner, provider)
      const protectedRoutes = ['/app', '/admin', '/agent', '/manager', '/tenant', '/owner', '/provider']
      const isProtectedRoute = protectedRoutes.some(route => path.startsWith(route))
      
      if (!isProtectedRoute){
        // skip refresh on public pages
        setLoading(false)
        return () => { mounted = false }
      }
    }catch(e){ /* ignore */ }

    authService.refresh().then(u=>{ if(mounted) setUser(u)}).catch(()=>{/* not authenticated */}).finally(()=>mounted && setLoading(false))
    return ()=>{mounted=false}
  },[])

  const login = async (email:string,password:string)=>{
    setLoading(true)
    try{
      const res = await authService.login(email,password)
      setUser(res.user)
      return res
    }finally{setLoading(false)}
  }

  const register = async (email:string,password:string,full_name?:string)=>{
    setLoading(true)
    try{
      await authService.register(email,password,full_name)
    }finally{setLoading(false)}
  }

  const logout = ()=>{
    authService.logout().finally(()=>{
      setUser(null)
    })
  }

  const hasRole = (role: UserRole): boolean => {
    if (!user) return false
    if (user.role === role) return true
    if (user.roles_csv) {
      return user.roles_csv.split(',').map(r => r.trim()).includes(role)
    }
    return false
  }

  const hasAnyRole = (roles: UserRole[]): boolean => {
    if (!user) return false
    return roles.some(role => hasRole(role))
  }

  const getDashboardPath = (): string => {
    if (!user) return '/login'
    
    switch (user.role) {
      case 'admin':
        return '/admin/dashboard'
      case 'manager':
        return '/manager/dashboard'
      case 'owner':
        return '/owner/dashboard'
      case 'agent':
        return '/agent/dashboard'
      case 'tenant':
        return '/tenant/dashboard'
      case 'service_provider':
        return '/provider/dashboard'
      case 'user':
      default:
        return '/app'
    }
  }

  return (
    <AuthContext.Provider value={{user,loading,login,register,logout,hasRole,hasAnyRole,getDashboardPath}}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(){
  const ctx = useContext(AuthContext)
  if(!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
