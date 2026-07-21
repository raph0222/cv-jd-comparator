<template>
  <section class="mt-4 rounded-lg border border-slate-300 bg-white p-4">
    <h2 class="text-sm font-semibold text-slate-800">Find best candidates</h2>
    <p class="mt-1 text-xs text-slate-600">
      Pick a stored job description. The system shortlists the closest resumes and ranks the top
      matches with a full analysis.
    </p>

    <div class="mt-3 flex flex-col gap-2 sm:flex-row sm:items-end">
      <div class="flex-1">
        <label for="jd-select" class="mb-1 block text-xs font-medium text-slate-700">
          Job description
        </label>
        <select
          id="jd-select"
          v-model="selectedId"
          class="w-full rounded-md border border-slate-300 bg-white p-2 text-xs text-slate-800 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-400"
          :disabled="ragLoading || jobDescriptions.length === 0"
        >
          <option value="" disabled>
            {{ jobDescriptions.length ? 'Select a job description' : 'No job descriptions yet' }}
          </option>
          <option v-for="jd in jobDescriptions" :key="jd.id" :value="jd.id">
            {{ jd.title }}
          </option>
        </select>
      </div>
      <button
        type="button"
        :disabled="ragLoading || !selectedId || isBackendOffline"
        class="rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold tracking-wide text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        @click="onFind"
      >
        {{ ragLoading ? 'SEARCHING...' : 'Find candidates' }}
      </button>
    </div>
  </section>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { FETCH_JOB_DESCRIPTIONS, FIND_BEST_CANDIDATES } from '../../store/types.js'

export default {
  name: 'JobDescriptionSelector',
  data() {
    return {
      selectedId: ''
    }
  },
  computed: {
    ...mapGetters(['isBackendOffline']),
    ...mapGetters('rag', ['jobDescriptions', 'ragLoading'])
  },
  created() {
    if (this.isBackendOffline) return
    this.fetchJobDescriptions().catch(() => {})
  },
  methods: {
    ...mapActions('rag', {
      fetchJobDescriptions: FETCH_JOB_DESCRIPTIONS,
      findBestCandidates: FIND_BEST_CANDIDATES
    }),
    onFind() {
      if (!this.selectedId) return
      this.findBestCandidates({ jd_id: this.selectedId }).catch(() => {})
    }
  }
}
</script>
