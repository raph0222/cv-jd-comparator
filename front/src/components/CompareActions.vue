<template>
  <div class="mt-4 flex justify-center">
    <button
      type="button"
      :disabled="isLoading || isFillingExamples"
      class="rounded-md bg-slate-900 px-4 py-2 text-xs font-semibold tracking-wide text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
      @click="$emit('compare')"
    >
      {{ isLoading ? 'COMPARING...' : 'COMPARE' }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'CompareActions',
  props: {
    isLoading: {
      type: Boolean,
      default: false
    },
    isFillingExamples: {
      type: Boolean,
      default: false
    }
  },
  emits: ['compare']
}
</script>
