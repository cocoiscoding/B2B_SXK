<template>
  <div class="iframe-container">
    <iframe
      :src="src"
      frameborder="0"
      class="iframe"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  routerPath: {
    type: String,
    default: ''
  }
})
const src = props.routerPath || ''
</script>

<style lang="scss" scoped>
.iframe-container {
  width: 100%;
  height: 100%;
}
.iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
