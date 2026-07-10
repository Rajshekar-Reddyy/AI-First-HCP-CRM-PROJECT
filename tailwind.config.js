export default {
  darkMode: "class",
  content: ["./index.html", "./*.jsx", "./*.js"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"]
      },
      colors: {
        cloud: "#f7f9fc",
        brand: "#2563eb",
        mint: "#0f9f6e",
        coral: "#e25555",
        amber: "#b7791f"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};
