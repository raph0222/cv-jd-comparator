<template>
  <section class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
    <div>
      <label for="job" class="mb-1 block text-xs font-medium text-slate-700">Job description</label>
      <textarea
        id="job"
        :value="job"
        placeholder="Paste the full job description here..."
        class="min-h-56 w-full rounded-md border border-slate-300 bg-white p-2.5 text-xs leading-5 text-slate-800 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-400"
        :disabled="disabled"
        @input="$emit('update:job', $event.target.value)"
      />
    </div>
    <div>
      <label for="resume" class="mb-1 block text-xs font-medium text-slate-700"
        >Candidate resume</label
      >
      <textarea
        id="resume"
        :value="resume"
        placeholder="Paste the candidate's resume here..."
        class="min-h-56 w-full rounded-md border border-slate-300 bg-white p-2.5 text-xs leading-5 text-slate-800 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-1 focus:ring-slate-400"
        :disabled="disabled"
        @input="$emit('update:resume', $event.target.value)"
      />
    </div>
  </section>
</template>

<script>
export default {
  name: 'CompareInputs',
  props: {
    job: {
      type: String,
      required: true
    },
    resume: {
      type: String,
      required: true
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:job', 'update:resume']
}
</script>
