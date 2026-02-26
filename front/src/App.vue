<template>
  <div class="flex min-h-screen flex-col bg-slate-50">
    <main class="mx-auto w-full max-w-4xl flex-1 px-4 py-5 md:px-6 md:py-6">
      <h1 class="text-2xl font-semibold tracking-tight text-slate-900 md:text-3xl">
        Resume/JD Comparator
      </h1>
      <p class="mt-2 text-sm text-slate-600">
        Paste the job description and the candidate's resume, then click Compare to see the match.
      </p>
      <div class="mt-4">
        <button
          type="button"
          :disabled="isLoading || isFillingExamples"
          class="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
          @click="onFillExamples"
        >
          Test with a fake resume and a random job description.
        </button>
      </div>

      <CompareInputs
        v-model:job="job"
        v-model:resume="resume"
        :disabled="isLoading || isFillingExamples"
      />

      <CompareActions
        :is-loading="isLoading"
        :is-filling-examples="isFillingExamples"
        @compare="onCompare"
      />

      <CompareResult
        :has-result="hasResult"
        :is-error="isError"
        :match-score="matchScore"
        :message="message"
        :qualification-scores="qualificationScores"
      />
    </main>
    <footer class="mx-auto mb-4 w-full max-w-4xl px-4 md:px-6">
      <p class="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
        For now, any text you paste here may be sent to the AI as-is. Be aware if you use external
        AI provider.
      </p>
    </footer>
  </div>
</template>

<script>
import CompareActions from './components/CompareActions.vue'
import CompareInputs from './components/CompareInputs.vue'
import CompareResult from './components/CompareResult.vue'
import { compareCv, loadExampleTexts } from './services/compareApi'
import { toUserMessage } from './services/errorInterface'

export default {
  name: 'App',
  components: {
    CompareActions,
    CompareInputs,
    CompareResult
  },
  data() {
    return {
      job: '',
      resume: '',
      isLoading: false,
      isFillingExamples: false,
      isError: false,
      hasResult: false,
      matchScore: null,
      message: '',
      qualificationScores: []
    }
  },
  computed: {
    apiBase() {
      return (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000').replace(/\/+$/, '')
    }
  },
  methods: {
    normalizeScores(raw) {
      if (!Array.isArray(raw)) return []
      return raw
        .map((item) => ({
          qualification: String(item?.qualification || '').trim(),
          match_score: Number.isFinite(Number(item?.match_score))
            ? Math.max(0, Math.min(100, Number(item.match_score)))
            : 0,
          reasoning: String(item?.reasoning || '').trim()
        }))
        .filter((item) => item.qualification.length > 0)
    },
    resetResultState() {
      this.isError = false
      this.hasResult = false
      this.matchScore = null
      this.message = ''
      this.qualificationScores = []
    },
    async onFillExamples() {
      this.isFillingExamples = true
      try {
        const { jobDescription, resume } = await loadExampleTexts()
        this.job = jobDescription
        this.resume = resume
        this.resetResultState()
      } catch (error) {
        this.isError = true
        this.hasResult = true
        this.matchScore = null
        this.message = toUserMessage(error)
        this.qualificationScores = []
      } finally {
        this.isFillingExamples = false
      }
    },
    async onCompare() {
      const job = this.job.trim()
      const resume = this.resume.trim()
      if (!job || !resume) {
        this.isError = true
        this.hasResult = true
        this.matchScore = null
        this.message = 'Please enter both job description and resume.'
        this.qualificationScores = []
        return
      }

      this.isLoading = true
      this.isError = false
      this.hasResult = true
      this.matchScore = null
      this.message = 'Comparing...'
      this.qualificationScores = []

      try {
        const data = await compareCv({
          apiBase: this.apiBase,
          jobDescription: job,
          resume
        })
        this.isError = false
        this.matchScore = data.matchScore
        this.message = data.reasoning
        this.qualificationScores = this.normalizeScores(data.qualificationScores)
      } catch (error) {
        this.isError = true
        this.message = toUserMessage(error)
        this.qualificationScores = []
      } finally {
        this.isLoading = false
      }
    }
  }
}
</script>
