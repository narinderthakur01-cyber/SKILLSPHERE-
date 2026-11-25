/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Obsidian Charcoal × Oxblood System
        charcoal: {
          DEFAULT: '#1B1A1B',
          50: '#F4F4F4',
          100: '#E5E4E5',
          200: '#C7C5C7',
          300: '#A4A1A4',
          400: '#6E6B6E',
          500: '#464446',
          600: '#323132',
          700: '#252425',
          800: '#1B1A1B',
          900: '#131213',
          950: '#0B0A0B',
        },
        deepslate: {
          DEFAULT: '#373034',
          50: '#F7F6F7',
          100: '#ECE9EB',
          200: '#DAD4D8',
          300: '#BDB4BA',
          400: '#8A7F87',
          500: '#5F545C',
          600: '#463D43',
          700: '#373034',
          800: '#282326',
          900: '#1C181B',
        },
        oxblood: {
          DEFAULT: '#914F51',
          50: '#FAF3F3',
          100: '#F4E5E5',
          200: '#E7C8C9',
          300: '#D5A4A6',
          400: '#BA7476',
          500: '#914F51',
          600: '#7B3F41',
          700: '#643233',
          800: '#4E2627',
          900: '#381A1B',
        },
        dustyrose: {
          DEFAULT: '#C5A49B',
          50: '#FAF7F6',
          100: '#F4EDED',
          200: '#E6D7D3',
          300: '#D8C1BA',
          400: '#C5A49B',
          500: '#A88379',
          600: '#87655C',
          700: '#674C45',
          800: '#4A3631',
          900: '#30221E',
        },
        warmivory: {
          DEFAULT: '#EFE9E3',
          50: '#FDFCFA',
          100: '#FAF7F4',
          200: '#EFE9E3',
          300: '#DFD5CA',
          400: '#CABDAC',
          500: '#B0A18F',
          600: '#918270',
        },
        // Functional Colors
        success: {
          DEFAULT: '#829B88',
          50: '#F4F7F5',
          100: '#E5EDE7',
          500: '#829B88',
          600: '#68826F',
          700: '#516757',
        },
        warning: {
          DEFAULT: '#C49A62',
          50: '#FAF7F2',
          100: '#F4ECE0',
          500: '#C49A62',
          600: '#AA8047',
          700: '#876434',
        },
        danger: {
          DEFAULT: '#B76565',
          50: '#FAF4F4',
          100: '#F5E7E7',
          500: '#B76565',
          600: '#9E4F4F',
          700: '#7E3C3C',
        },
        // Semantic Compatibility Mappings & System Tokens
        ivory: {
          DEFAULT: '#EFE9E3',
          warm: '#FAF7F4',
          light: '#FDFCFA',
        },
        rose: {
          DEFAULT: '#C5A49B',
          50: '#FAF7F6',
          100: '#F4EDED',
          200: '#E6D7D3',
          300: '#D8C1BA',
          400: '#C5A49B',
          500: '#A88379',
        },
        'charcoal-light': '#262124',
        'charcoal-hover': '#2E282C',
        'ivory-warm': '#FAF7F4',
        slate: {
          DEFAULT: '#373034',
        },
        copper: {
          DEFAULT: '#914F51',
        },
        mint: {
          DEFAULT: '#829B88',
        },
        porcelain: {
          DEFAULT: '#EFE9E3',
        },
        graphite: {
          DEFAULT: '#1B1A1B',
        },
        forest: {
          DEFAULT: '#1B1A1B',
        },
        orange: {
          DEFAULT: '#914F51',
        },
        brand: {
          DEFAULT: '#914F51',
          500: '#914F51',
          600: '#7B3F41',
        }
      },
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'liquid-subtle': '0 4px 20px -2px rgba(0, 0, 0, 0.25), inset 0 1px 0 0 rgba(239, 233, 227, 0.08)',
        'liquid-panel': '0 12px 36px -4px rgba(0, 0, 0, 0.45), inset 0 1px 1px 0 rgba(197, 164, 155, 0.12)',
        'liquid-elevated': '0 24px 56px -12px rgba(0, 0, 0, 0.65), inset 0 1px 1px 0 rgba(239, 233, 227, 0.15)',
        'liquid-oxblood': '0 8px 30px -4px rgba(145, 79, 81, 0.4), inset 0 1px 0 0 rgba(239, 233, 227, 0.25)',
        'liquid-light': '0 10px 30px -4px rgba(27, 26, 27, 0.07), inset 0 1px 0 0 rgba(255, 255, 255, 0.85)',
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.16, 1, 0.3, 1)',
        'liquid': 'cubic-bezier(0.22, 1, 0.36, 1)',
      }
    },
  },
  plugins: [],
}