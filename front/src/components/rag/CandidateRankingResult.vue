<template>
  <section class="mt-4">
    <div
      v-if="ragError"
      class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
    >
      {{ ragErrorMessage }}
    </div>

    <div
      v-else-if="ragLoading"
      class="rounded-lg border border-slate-300 bg-white p-3 text-sm text-slate-600"
    >
      Searching and ranking candidates...
    </div>

    <div v-else-if="hasResults" class="space-y-3">
      <article
        v-for="candidate in candidateResults"
        :key="candidate.resume_id"
        class="rounded-lg border border-slate-300 bg-white p-3"
      >
        <header class="flex items-baseline justify-between">
          <div class="flex items-baseline gap-2">
            <span class="text-xs font-semibold text-slate-500">#{{ candidate.rank }}</span>
            <h3 class="text-sm font-semibold text-slate-800">
              {{ candidate.candidate_name || 'Unnamed candidate' }}
            </h3>
          </div>
          <span :class="['text-2xl font-semibold', scoreColorClass(candidate.match_score)]">
            {{ candidate.match_score }}%
          </span>
        </header>

        <p class="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-600">
          {{ candidate.reasoning }}
        </p>

        <div class="mt-2 flex flex-wrap gap-3 text-xs">
          <p v-if="candidate.seniority_fit" class="text-slate-600">
            <span class="font-medium text-slate-700">Seniority fit:</span>
            {{ candidate.seniority_fit }}
          </p>
        </div>

        <div class="mt-2 flex flex-wrap gap-1.5" v-if="hasItems(candidate.matching_skills)">
          <span
            v-for="(skill, idx) in candidate.matching_skills"
            :key="`m-${idx}`"
            class="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700"
          >
            {{ skill }}
          </span>
        </div>
        <div class="mt-1.5 flex flex-wrap gap-1.5" v-if="hasItems(candidate.missing_skills)">
          <span
            v-for="(skill, idx) in candidate.missing_skills"
            :key="`x-${idx}`"
            class="rounded bg-rose-50 px-2 py-0.5 text-xs text-rose-700"
          >
            {{ skill }}
          </span>
        </div>

        <div
          v-if="hasItems(candidate.qualification_scores)"
          class="mt-3 border-t border-slate-200 pt-2"
        >
          <div
            v-for="(item, idx) in candidate.qualification_scores"
            :key="`${item.qualification}-${idx}`"
            class="border-b border-slate-100 py-2 last:border-b-0"
          >
            <p class="text-sm font-medium text-slate-800">{{ item.qualification }}</p>
            <p class="mt-1 text-xs leading-5 text-slate-600">
              <span :class="['mr-1 font-semibold', scoreColorClass(item.match_score)]"
                >{{ item.match_score }}%</span
              >
              <span>{{ item.reasoning }}</span>
            </p>
          </div>
        </div>
      </article>
    </div>

    <div
      v-else-if="searched"
      class="rounded-lg border border-slate-300 bg-white p-3 text-sm text-slate-600"
    >
      No matching candidates found. Add some resumes to the database first.
    </div>
  </section>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'CandidateRankingResult',
  computed: {
    ...mapGetters('rag', ['candidateResults', 'ragLoading', 'ragError', 'ragErrorMessage']),
    hasResults() {
      return Array.isArray(this.candidateResults) && this.candidateResults.length > 0
    },
    searched() {
      // A search ran (results array is set) but came back empty.
      return Array.isArray(this.candidateResults)
    }
  },
  methods: {
    hasItems(value) {
      return Array.isArray(value) && value.length > 0
    },
    scoreColorClass(score) {
      if (!Number.isFinite(Number(score))) return 'text-slate-700'
      const normalized = Math.max(0, Math.min(100, Number(score)))
      if (normalized > 80) return 'text-emerald-700'
      if (normalized > 50) return 'text-amber-700'
      return 'text-rose-700'
    }
  }
}
</script>
