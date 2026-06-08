import axios from '../../axios/axios.js'
import { handleErrorMessage } from '../../utils.js'
import {
  FETCH_JOB_DESCRIPTIONS,
  FETCH_RESUMES,
  FIND_BEST_CANDIDATES,
  INGEST_JD,
  INGEST_RESUME,
  RAG_ERROR,
  RAG_REQUEST,
  RAG_RESET_RESULTS,
  RAG_SET_CANDIDATES,
  RAG_SET_JOB_DESCRIPTIONS,
  RAG_SET_RESUMES
} from '../types.js'

const mutations = {
  [RAG_REQUEST](state) {
    state.loading = true
    state.error = false
    state.errorMessage = ''
  },
  [RAG_ERROR](state, { message }) {
    state.loading = false
    state.error = true
    state.errorMessage = message
  },
  [RAG_SET_JOB_DESCRIPTIONS](state, { jobDescriptions }) {
    state.loading = false
    state.error = false
    state.errorMessage = ''
    state.jobDescriptions = jobDescriptions
  },
  [RAG_SET_RESUMES](state, { resumes }) {
    state.loading = false
    state.error = false
    state.errorMessage = ''
    state.resumes = resumes
  },
  [RAG_SET_CANDIDATES](state, { candidateResults }) {
    state.loading = false
    state.error = false
    state.errorMessage = ''
    state.candidateResults = candidateResults
  },
  [RAG_RESET_RESULTS](state) {
    state.candidateResults = []
    state.error = false
    state.errorMessage = ''
  }
}

const actions = {
  [FETCH_JOB_DESCRIPTIONS]({ commit }) {
    commit(RAG_REQUEST)
    return axios
      .get('/api/v1/job-descriptions')
      .then((resp) => {
        const jobDescriptions = resp.data?.data?.job_descriptions ?? []
        commit(RAG_SET_JOB_DESCRIPTIONS, { jobDescriptions })
        return jobDescriptions
      })
      .catch((err) => {
        commit(RAG_ERROR, { message: handleErrorMessage(err) })
        return Promise.reject(err)
      })
  },
  [FETCH_RESUMES]({ commit }) {
    commit(RAG_REQUEST)
    return axios
      .get('/api/v1/resumes')
      .then((resp) => {
        const resumes = resp.data?.data?.resumes ?? []
        commit(RAG_SET_RESUMES, { resumes })
        return resumes
      })
      .catch((err) => {
        commit(RAG_ERROR, { message: handleErrorMessage(err) })
        return Promise.reject(err)
      })
  },
  [INGEST_RESUME]({ commit, dispatch }, { candidate_name, content }) {
    commit(RAG_REQUEST)
    return axios
      .post('/api/v1/resumes', { candidate_name, content })
      .then((resp) => {
        dispatch(FETCH_RESUMES)
        return resp.data?.data
      })
      .catch((err) => {
        commit(RAG_ERROR, { message: handleErrorMessage(err) })
        return Promise.reject(err)
      })
  },
  [INGEST_JD]({ commit, dispatch }, { title, content }) {
    commit(RAG_REQUEST)
    return axios
      .post('/api/v1/job-descriptions', { title, content })
      .then((resp) => {
        dispatch(FETCH_JOB_DESCRIPTIONS)
        return resp.data?.data
      })
      .catch((err) => {
        commit(RAG_ERROR, { message: handleErrorMessage(err) })
        return Promise.reject(err)
      })
  },
  [FIND_BEST_CANDIDATES]({ commit }, { jd_id }) {
    commit(RAG_REQUEST)
    commit(RAG_RESET_RESULTS)
    return axios
      .post(`/api/v1/job-descriptions/${jd_id}/find-candidates`)
      .then((resp) => {
        const candidateResults = resp.data?.data?.candidates ?? []
        commit(RAG_SET_CANDIDATES, { candidateResults })
        return resp.data?.data
      })
      .catch((err) => {
        commit(RAG_ERROR, { message: handleErrorMessage(err) })
        return Promise.reject(err)
      })
  }
}

const getters = {
  jobDescriptions: (state) => state.jobDescriptions,
  resumes: (state) => state.resumes,
  candidateResults: (state) => state.candidateResults,
  ragLoading: (state) => state.loading,
  ragError: (state) => state.error,
  ragErrorMessage: (state) => state.errorMessage
}

export default {
  namespaced: true,
  state: () => ({
    jobDescriptions: [],
    resumes: [],
    candidateResults: null,
    loading: false,
    error: false,
    errorMessage: ''
  }),
  mutations,
  actions,
  getters
}
