import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        instacart: {
          green: '#43B02A',
          'green-dark': '#2D8A1E',
          'green-light': '#E8F5E3',
          dark: '#343538',
          grey: '#767676',
          'grey-light': '#F7F7F7',
          border: '#E8E8E8',
          purple: '#8B5CF6',
          'purple-light': '#EDE9FE',
          blue: '#3B82F6',
          // Dark mode variants
          'dark-bg': '#1F2937',
          'dark-card': '#374151',
          'dark-border': '#4B5563',
          'dark-text': '#F9FAFB',
          'dark-text-secondary': '#9CA3AF',
        },
      },
      borderRadius: {
        'instacart': '12px',
      },
      boxShadow: {
        'instacart': '0 1px 3px rgba(0, 0, 0, 0.08)',
        'instacart-hover': '0 4px 12px rgba(67, 176, 42, 0.15)',
      },
    },
  },
  plugins: [],
}
export default config
