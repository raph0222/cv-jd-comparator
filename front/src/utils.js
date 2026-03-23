import { API_ERROR_MESSAGES, GENERIC_ERROR_MESSAGE } from './constants'

// Builds the user-visible error string from an Axios error after a failed request.
export function handleErrorMessage(err) {
  const apiCode = err.response?.data?.error?.code || GENERIC_ERROR_MESSAGE
  const key = String(apiCode).trim()
  return API_ERROR_MESSAGES[key]
}
