import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'
import typography from '@tailwindcss/typography'

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FAFAFA',
        primaryAccent: '#18181B',
        brand: '#FF4017',
        background: {
          DEFAULT: '#111113',
          secondary: '#27272A'
        },
        secondary: '#f5f5f5',
        border: 'rgba(var(--color-border-default))',
        accent: '#27272A',
        muted: '#A1A1AA',
        destructive: '#E53935',
        positive: '#22C55E'
      },
      fontFamily: {
        geist: 'var(--font-geist-sans)',
        dmmono: 'var(--font-dm-mono)'
      },
      borderRadius: {
        xl: '10px'
      },
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-body': '#FAFAFA',
            '--tw-prose-headings': '#FAFAFA',
            '--tw-prose-bold': '#FAFAFA',
            '--tw-prose-links': '#FAFAFA',
            '--tw-prose-code': '#FAFAFA',
            '--tw-prose-counters': '#A1A1AA',
            '--tw-prose-bullets': '#A1A1AA',
            '--tw-prose-hr': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-th-borders': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-td-borders': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-pre-bg': '#27272A',
            '--tw-prose-pre-code': '#FAFAFA',
            '--tw-prose-quotes': '#A1A1AA',
            '--tw-prose-quote-borders': 'rgba(255, 255, 255, 0.2)',
          }
        }
      }
    }
  },
  plugins: [tailwindcssAnimate, typography]
} satisfies Config
