import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { api } from '../services/api.js'

const AuthContext = createContext(null)
const USER_KEY = 'researchgpt.user'

function readStoredUser() {
  try { return JSON.parse(window.sessionStorage.getItem(USER_KEY) ?? 'null') }
  catch { return null }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readStoredUser)
  const [ready, setReady] = useState(false)

  function clearSession() {
    window.sessionStorage.removeItem('researchgpt.accessToken')
    window.sessionStorage.removeItem(USER_KEY)
    setUser(null)
  }

  useEffect(() => {
    const handleUnauthorized = () => clearSession()
    window.addEventListener('researchgpt:unauthorized', handleUnauthorized)
    const token = window.sessionStorage.getItem('researchgpt.accessToken')
    if (!token) {
      clearSession()
      setReady(true)
      return () => window.removeEventListener('researchgpt:unauthorized', handleUnauthorized)
    }
    api.get('/auth/me')
      .then(({ data }) => { setUser(data); window.sessionStorage.setItem(USER_KEY, JSON.stringify(data)) })
      .catch(clearSession)
      .finally(() => setReady(true))
    return () => window.removeEventListener('researchgpt:unauthorized', handleUnauthorized)
  }, [])

  async function authenticate(mode, values) {
    const { data } = await api.post(`/auth/${mode}`, values)
    window.sessionStorage.setItem('researchgpt.accessToken', data.access_token)
    window.sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
    setUser(data.user)
    return data.user
  }

  async function logout() {
    try { await api.post('/auth/logout') }
    finally { clearSession() }
  }

  async function updateProfile(values) {
    const { data } = await api.patch('/auth/me', values)
    setUser(data)
    window.sessionStorage.setItem(USER_KEY, JSON.stringify(data))
    return data
  }

  const value = useMemo(() => ({ user, ready, authenticate, logout, updateProfile }), [user, ready])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
