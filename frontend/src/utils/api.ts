import axios from 'axios'
import { useAppStore } from '../store'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// Добавляем Bearer токен ко всем запросам
api.interceptors.request.use((config) => {
  const token = useAppStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// При 401 сбрасываем токен → App.tsx пересоздаст авторизацию
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      useAppStore.getState().setToken(null)
    }
    return Promise.reject(err)
  }
)

export default api
