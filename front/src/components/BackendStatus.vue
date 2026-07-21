<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium',
      isBackendOffline
        ? 'border-rose-200 bg-rose-50 text-rose-700'
        : 'border-emerald-200 bg-emerald-50 text-emerald-700'
    ]"
    :title="
      isBackendOffline
        ? 'The backend server is currently switched off.'
        : 'The backend server is running.'
    "
  >
    <span
      :class="[
        'h-2 w-2 rounded-full',
        isBackendOffline ? 'bg-rose-500' : 'animate-pulse bg-emerald-500'
      ]"
    />
    {{ isBackendOffline ? 'Demo offline' : 'Live' }}
  </span>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'BackendStatus',
  computed: {
    ...mapGetters(['isBackendOffline'])
  }
}
</script>
