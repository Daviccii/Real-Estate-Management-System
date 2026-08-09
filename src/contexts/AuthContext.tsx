import React, { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '../services/auth'

type User = any

type AuthContextType = {
  user: User | null
  loading: boolean
  login: (email:string,password:string)=>Promise<void>
  register: (email:string,password:string,full_name?:string)=>Promise<void>
  logout: ()=>void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{children:React.ReactNode}> = ({children}) =>{
  const [user,setUser] = useState<User | null>(null)
  const [loading,setLoading] = useState(true)

  useEffect(()=>{
    let mounted=true
    authService.refresh().then(u=>{ if(mounted) setUser(u)}).catch(()=>{/* not authenticated */}).finally(()=>mounted && setLoading(false))
    return ()=>{mounted=false}
  },[])

  const login = async (email:string,password:string)=>{
    setLoading(true)
    try{
      const u = await authService.login(email,password)
      setUser(u)
    }finally{setLoading(false)}
  }

  const register = async (email:string,password:string,full_name?:string)=>{
    setLoading(true)
    try{
      await authService.register(email,password,full_name)
    }finally{setLoading(false)}
  }

  const logout = ()=>{
    authService.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{user,loading,login,register,logout}}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(){
  const ctx = useContext(AuthContext)
  if(!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
