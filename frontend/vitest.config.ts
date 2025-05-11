import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true, // This will make vi accessible globally
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["**/__tests__/*.{test,spec}.{ts,tsx}"],
    coverage: {
      reporter: ["text", "json", "html"],
    },
  },
});
