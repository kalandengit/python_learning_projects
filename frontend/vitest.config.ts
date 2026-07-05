import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    environmentOptions: { jsdom: { url: "http://localhost/" } },
    // Under vitest the global Request is undici's, which needs an absolute URL;
    // give the client an absolute API base so relative prefixes resolve.
    env: { VITE_API_BASE_URL: "http://localhost/api/v1" },
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});
