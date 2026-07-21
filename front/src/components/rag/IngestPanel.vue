<template>
  <section class="rounded-lg border border-slate-300 bg-white p-4">
    <h2 class="text-sm font-semibold text-slate-800">Add a JD/Resume to the system</h2>

    <div class="mt-3 inline-flex rounded-md border border-slate-300 p-0.5 text-xs">
      <button type="button" :class="tabClass('resume')" @click="docType = 'resume'">Resume</button>
      <button type="button" :class="tabClass('jd')" @click="docType = 'jd'">Job description</button>
    </div>

    <div class="mt-3">
      <label class="mb-1 block text-xs font-medium text-slate-700">
        {{ isResume ? 'Candidate name' : 'Job title' }}
      </label>
      <input
        v-model="nameField"
        type="text"
        :placeholder="isResume ? 'e.g. John Doe' : 'e.g. Senior Python Developer'"
        class="w-full rounded-md border border-slate-300 bg-white p-2 text-xs text-slate-800 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-400"
        :disabled="ragLoading"
      />
    </div>

    <div class="mt-3">
      <label class="mb-1 block text-xs font-medium text-slate-700">
        {{ isResume ? 'Resume text' : 'Job description text' }}
      </label>
      <textarea
        v-model="content"
        :placeholder="isResume ? 'Paste the resume here...' : 'Paste the job description here...'"
        class="min-h-40 w-full rounded-md border border-slate-300 bg-white p-2.5 text-xs leading-5 text-slate-800 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-400"
        :disabled="ragLoading"
      />
    </div>

    <p v-if="ragError" class="mt-2 text-xs text-rose-700">{{ ragErrorMessage }}</p>
    <p v-if="successMessage" class="mt-2 text-xs text-emerald-700">{{ successMessage }}</p>

    <div class="mt-3 flex justify-end">
      <button
        type="button"
        :disabled="ragLoading || !canSubmit || isBackendOffline"
        class="rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold tracking-wide text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
        @click="onSubmit"
      >
        {{ ragLoading ? 'ADDING...' : 'Add' }}
      </button>
    </div>
  </section>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'
import { INGEST_JD, INGEST_RESUME } from '../../store/types.js'

export default {
  name: 'IngestPanel',
  data() {
    return {
      docType: 'resume',
      nameField: '',
      content: '',
      successMessage: ''
    }
  },
  computed: {
    ...mapGetters(['isBackendOffline']),
    ...mapGetters('rag', ['ragLoading', 'ragError', 'ragErrorMessage']),
    isResume() {
      return this.docType === 'resume'
    },
    canSubmit() {
      return Boolean(this.content.trim())
    }
  },
  methods: {
    ...mapActions('rag', { ingestResume: INGEST_RESUME, ingestJd: INGEST_JD }),
    tabClass(type) {
      const active = this.docType === type
      return [
        'rounded px-3 py-1 font-medium transition',
        active ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'
      ]
    },
    onSubmit() {
      this.successMessage = ''
      const content = this.content.trim()
      const name = this.nameField.trim()
      if (!content) return

      const request = this.isResume
        ? this.ingestResume({ candidate_name: name, content })
        : this.ingestJd({ title: name, content })

      request
        .then(() => {
          this.successMessage = this.isResume
            ? 'Resume added to the database.'
            : 'Job description added to the database.'
          this.nameField = ''
          this.content = ''
        })
        .catch(() => {})
    }
  }
}
</script>
