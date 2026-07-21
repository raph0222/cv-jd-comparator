import { API_ERROR_MESSAGES, GENERIC_ERROR_MESSAGE } from './constants'

// Build-time switch. Set VITE_BACKEND_OFFLINE=true to trigger the "offline" mode.
export const isBackendOffline = import.meta.env.VITE_BACKEND_OFFLINE === 'true'

// Builds the user-visible error string from an Axios error after a failed request.
export function handleErrorMessage(err) {
  const apiCode = err.response?.data?.error?.code || GENERIC_ERROR_MESSAGE
  const key = String(apiCode).trim()
  return API_ERROR_MESSAGES[key]
}
