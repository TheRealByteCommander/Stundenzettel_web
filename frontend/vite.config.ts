import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Wichtig: Wir setzen den Build-Output-Ordner auf "build",
// damit er mit dem Deploy-Skript auf dem Server übereinstimmt
// (dort wird "/frontend/build" erwartet, nicht "dist").
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
  },
})
