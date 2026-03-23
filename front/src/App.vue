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
          :disabled="isLoading || isExamplesLoading"
          class="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
          @click="onFillExamples"
        >
          Test with a fake resume and a random job description.
        </button>
      </div>

      <CompareInputs
        v-model:job="job"
        v-model:resume="resume"
        :disabled="isLoading || isExamplesLoading"
      />

      <CompareActions @compare="onCompare" />

      <CompareResult />
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
import { mapGetters } from 'vuex'
import CompareActions from './components/CompareActions.vue'
import CompareInputs from './components/CompareInputs.vue'
import CompareResult from './components/CompareResult.vue'
import {
  COMPARE_PANEL_OPEN,
  COMPARE_RESET,
  COMPARE_VALIDATION_ERROR,
  LOAD_EXAMPLE_TEXTS,
  RUN_COMPARE
} from './store/types.js'

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
      resume: ''
    }
  },
  computed: {
    ...mapGetters(['isLoading', 'isExamplesLoading'])
  },
  methods: {
    checkInputs() {
      return Boolean(this.job.trim() && this.resume.trim())
    },
    onFillExamples() {
      this.$store
        .dispatch(LOAD_EXAMPLE_TEXTS)
        .then(({ jobDescription, resume }) => {
          this.job = jobDescription
          this.resume = resume
        })
        .catch(() => {})
    },
    onCompare() {
      this.$store.commit(COMPARE_RESET)
      this.$store.commit(COMPARE_PANEL_OPEN)

      if (!this.checkInputs()) {
        this.$store.commit(COMPARE_VALIDATION_ERROR, {
          message: 'Please enter both job description and resume.'
        })
        return
      }

      const job_description = this.job.trim()
      const resume = this.resume.trim()
      this.$store.dispatch(RUN_COMPARE, { job_description, resume }).catch(() => {})
    }
  }
}
</script>
