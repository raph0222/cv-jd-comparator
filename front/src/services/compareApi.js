function buildApiUrl(apiBase, path) {
  const base = String(apiBase || 'http://localhost:5000').replace(/\/+$/, '')
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${cleanPath}`
}

async function readJsonSafely(response) {
  try {
    return await response.json()
  } catch {
    return null
  }
}

function createApiError({ code, message, status }) {
  const error = new Error(message || 'Request failed.')
  error.code = code || 'request_failed'
  error.status = status || 0
  error.message = message || 'Request failed.'
  return error
}

export async function compareCv({ apiBase, jobDescription, resume }) {
  try {
    const res = await fetch(buildApiUrl(apiBase, '/api/v1/compare'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_description: jobDescription,
        resume
      })
    })

    const json = await readJsonSafely(res)
    if (!res.ok) {
      const code = String(json?.error?.code || 'request_failed')
      const message = String(json?.error?.message || 'Request failed.')
      throw createApiError({ code, message, status: res.status })
    }

    const data = json?.data
    return {
      matchScore: typeof data?.match_score === 'number' ? data.match_score : null,
      reasoning: String(data?.reasoning || 'No explanation returned from model.'),
      qualificationScores: Array.isArray(data?.qualification_scores)
        ? data.qualification_scores
        : []
    }
  } catch (err) {
    if (err?.code) throw err
    throw createApiError({
      code: 'network_error',
      message: err?.message || 'Could not reach server.',
      status: 0
    })
  }
}

export async function loadExampleTexts() {
  const [jdRes, resumeRes] = await Promise.all([
    fetch('/job_description_example.txt'),
    fetch('/resume_example.txt')
  ])
  if (!jdRes.ok || !resumeRes.ok) {
    throw createApiError({
      code: 'request_failed',
      message: 'Could not load example files.',
      status: 400
    })
  }

  const [jobDescription, resume] = await Promise.all([jdRes.text(), resumeRes.text()])
  return {
    jobDescription: jobDescription.trim(),
    resume: resume.trim()
  }
}
