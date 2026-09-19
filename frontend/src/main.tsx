import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './app/router/AppRouter'
import './styles.css'

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>)
