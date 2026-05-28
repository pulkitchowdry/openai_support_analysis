import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        panel: "#f5f7f9",
        line: "#d8e0e6",
        accent: "#0f766e",
        warning: "#b45309"
      }
    }
  },
  plugins: []
};

export default config;
