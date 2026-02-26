<template>
  <section
    v-if="hasResult"
    :class="[
      'mt-5 rounded-lg border bg-white p-3',
      isError ? 'border-red-200 bg-red-50' : 'border-slate-300'
    ]"
  >
    <div :class="['text-3xl font-semibold', scoreColorClass(matchScore)]">
      {{ showPercent ? matchScore + '%' : '--%' }}
    </div>
    <p
      :class="[
        'mt-2 whitespace-pre-wrap text-sm leading-6',
        isError ? 'text-red-700' : 'text-slate-600'
      ]"
    >
      {{ message }}
    </p>

    <div v-if="hasQualificationScores" class="mt-3 border-t border-slate-200 pt-2">
      <div
        v-for="(item, idx) in qualificationScores"
        :key="`${item.qualification}-${idx}`"
        class="border-b border-slate-100 py-2"
      >
        <p class="text-sm font-medium text-slate-800">
          {{ item.qualification }}
        </p>
        <p class="mt-1 text-xs leading-5 text-slate-600">
          <span :class="['mr-1 font-semibold', scoreColorClass(item.match_score)]"
            >{{ item.match_score }}%</span
          >
          <span>{{ item.reasoning || 'No explanation provided.' }}</span>
        </p>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'CompareResult',
  props: {
    hasResult: {
      type: Boolean,
      default: false
    },
    isError: {
      type: Boolean,
      default: false
    },
    matchScore: {
      type: Number,
      default: null
    },
    message: {
      type: String,
      default: ''
    },
    qualificationScores: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    showPercent() {
      return !this.isError && typeof this.matchScore === 'number'
    },
    hasQualificationScores() {
      return (
        !this.isError &&
        Array.isArray(this.qualificationScores) &&
        this.qualificationScores.length > 0
      )
    }
  },
  methods: {
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
