/**
 * Messages for specific API `error.code` values from the backend.
 */
export const API_ERROR_MESSAGES = {
  bad_request: 'Please check your input and try again.',
  unsupported_media_type: 'The request must use JSON. Please try again.',
  job_description_too_long: 'The job description is too long. Shorten it and try again.',
  resume_too_long: 'The resume is too long. Shorten it and try again.',
  rate_limit_exceeded: 'Too many requests in a short time. Please wait and try again.',
  service_unavailable: 'Service is down, try again later.',
  error: 'Something went wrong. Please try again.'
}

export const GENERIC_ERROR_MESSAGE = API_ERROR_MESSAGES.error
