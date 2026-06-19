import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 550,
    rollupOptions: {
      output: {
        manualChunks: {
          maps: ["leaflet", "react-leaflet"],
          charts: ["recharts"],
          icons: ["lucide-react"],
        },
      },
    },
  },
});
