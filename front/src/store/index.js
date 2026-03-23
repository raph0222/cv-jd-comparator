import { createStore } from 'vuex'
import axios from '../axios/axios.js'
import { handleErrorMessage } from '../utils.js'
import {
  COMPARE_ERROR,
  COMPARE_PANEL_OPEN,
  COMPARE_REQUEST,
  COMPARE_RESET,
  COMPARE_SUCCESS,
  COMPARE_VALIDATION_ERROR,
  EXAMPLES_LOAD_ERROR,
  EXAMPLES_LOAD_REQUEST,
  EXAMPLES_LOAD_SUCCESS,
  LOAD_EXAMPLE_TEXTS,
  RUN_COMPARE
} from './types.js'

const mutations = {
  [COMPARE_RESET](state) {
    state.isLoading = false
    state.error = false
    state.errorMessage = ''
    state.isComparePanelOpen = false
    state.result = null
  },
  [COMPARE_PANEL_OPEN](state) {
    state.isComparePanelOpen = true
  },
  [COMPARE_REQUEST](state) {
    state.isLoading = true
    state.error = false
    state.errorMessage = ''
    state.result = null
  },
  [COMPARE_SUCCESS](state, { data }) {
    state.isLoading = false
    state.error = false
    state.errorMessage = ''
    state.result = data
  },
  [COMPARE_ERROR](state, { message }) {
    state.isLoading = false
    state.error = true
    state.errorMessage = message
    state.result = null
  },
  [COMPARE_VALIDATION_ERROR](state, { message }) {
    state.isLoading = false
    state.error = true
    state.errorMessage = message
    state.result = null
  },
  [EXAMPLES_LOAD_REQUEST](state) {
    state.isExamplesLoading = true
  },
  [EXAMPLES_LOAD_SUCCESS](state) {
    state.isExamplesLoading = false
  },
  [EXAMPLES_LOAD_ERROR](state, { message }) {
    state.isExamplesLoading = false
    state.error = true
    state.errorMessage = message
    state.isComparePanelOpen = true
    state.result = null
  }
}

const actions = {
  [RUN_COMPARE]: ({ commit }, { job_description, resume }) => {
    return new Promise((resolve, reject) => {
      commit(COMPARE_REQUEST)

      axios
        .post('/api/v1/compare', {
          job_description,
          resume
        })
        .then((resp) => {
          const data = resp.data?.data
          if (!data) {
            const message = handleErrorMessage(resp)
            commit(COMPARE_ERROR, { message })
            reject(resp)
            return
          }
          commit(COMPARE_SUCCESS, { data })
          resolve(resp)
        })
        .catch((err) => {
          const message = handleErrorMessage(err)
          commit(COMPARE_ERROR, { message })
          reject(err)
        })
    })
  },
  [LOAD_EXAMPLE_TEXTS]: ({ commit }) => {
    return new Promise((resolve, reject) => {
      commit(EXAMPLES_LOAD_REQUEST)

      Promise.all([
        axios.get('/job_description_example.txt', {
          responseType: 'text',
          validateStatus: (status) => status === 200
        }),
        axios.get('/resume_example.txt', {
          responseType: 'text',
          validateStatus: (status) => status === 200
        })
      ])
        .then(([jdRes, resumeRes]) => {
          commit(EXAMPLES_LOAD_SUCCESS)
          commit(COMPARE_RESET)
          resolve({
            jobDescription: String(jdRes.data).trim(),
            resume: String(resumeRes.data).trim()
          })
        })
        .catch((err) => {
          const message = handleErrorMessage(err)
          commit(EXAMPLES_LOAD_ERROR, { message })
          reject(err)
        })
    })
  }
}

const getters = {
  result: (state) => state.result,
  matchScore: (state) => state.result?.match_score || null,
  qualificationScores: (state) =>
    Array.isArray(state.result?.qualification_scores) ? state.result.qualification_scores : [],
  isLoading: (state) => state.isLoading,
  error: (state) => state.error,
  errorMessage: (state) => state.errorMessage,
  isComparePanelOpen: (state) => state.isComparePanelOpen,
  isExamplesLoading: (state) => state.isExamplesLoading
}

export default createStore({
  state: () => ({
    isLoading: false,
    error: false,
    errorMessage: '',
    isComparePanelOpen: false,
    result: null,
    isExamplesLoading: false
  }),
  mutations,
  actions,
  getters
})
