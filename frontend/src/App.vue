<template>
  <div id="app" class="d-flex flex-column min-vh-100 bg-light">
    <Navbar />

    <main class="container flex-grow-1 py-4 mb-4">
      <router-view />
    </main>

    <footer class="bg-dark text-white py-3 text-center small mt-auto border-top">
      <div class="container">
        🏔️ Trekking Management Application (TMA) — V2 | IITM BS Degree Project
      </div>
    </footer>
  </div>
</template>

<script setup>
import Navbar from '@/components/Navbar.vue'
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  scroll-behavior: smooth;
  overflow-x: hidden;
  max-width: 100vw;
}

body {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: #f8fafc;
  color: #0f172a;
}

.card {
  border-radius: 8px;
}

@media (max-width: 767.98px) {
  main.container {
    padding-left: 12px !important;
    padding-right: 12px !important;
    padding-top: 1rem !important;
  }
}
</style>

