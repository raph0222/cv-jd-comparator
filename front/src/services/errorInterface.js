const USER_MESSAGES_BY_CODE = {
  bad_request: 'Please provide both a job description and a resume.',
  job_description_too_long: 'The job description is too long for this endpoint configuration.',
  resume_too_long: 'The resume is too long for this endpoint configuration.',
  rate_limit_exceeded: 'Too many requests in a short time. Please wait and try again.',
  internal_error: 'The server encountered an internal error. Please try again later.',
  network_error: 'Network error: could not reach the server. Check backend availability.',
  request_failed: 'Request failed. Please try again.'
}

export function toUserMessage(error) {
  if (!error || typeof error !== 'object') {
    return 'Unexpected error. Please try again.'
  }

  const code = String(error.code || '').trim()
  const backendMessage = String(error.message || '').trim()
  if (code && USER_MESSAGES_BY_CODE[code]) {
    if (code === 'job_description_too_long' || code === 'resume_too_long') {
      return backendMessage || USER_MESSAGES_BY_CODE[code]
    }
    return USER_MESSAGES_BY_CODE[code]
  }

  if (backendMessage) return backendMessage
  return USER_MESSAGES_BY_CODE.request_failed
}
