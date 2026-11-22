import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? `http://${window.location.hostname}:8000/api/v1`,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = window.sessionStorage.getItem('researchgpt.accessToken')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url ?? ''
    if (error.response?.status === 401 && !url.startsWith('/auth/')) {
      window.dispatchEvent(new Event('researchgpt:unauthorized'))
    }
    return Promise.reject(error)
  },
)

