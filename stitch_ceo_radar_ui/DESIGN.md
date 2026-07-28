---
name: Executive Radar Dark
colors:
  surface: '#111317'
  surface-dim: '#111317'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#c0c7d3'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#8b919c'
  outline-variant: '#414751'
  surface-tint: '#9fcaff'
  primary: '#9fcaff'
  on-primary: '#003259'
  primary-container: '#4894e2'
  on-primary-container: '#002b4e'
  inverse-primary: '#0061a5'
  secondary: '#c1c6d7'
  on-secondary: '#2a303d'
  secondary-container: '#434957'
  on-secondary-container: '#b3b8c8'
  tertiary: '#bdc7dc'
  on-tertiary: '#273141'
  tertiary-container: '#8791a5'
  on-tertiary-container: '#202a3a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d2e4ff'
  primary-fixed-dim: '#9fcaff'
  on-primary-fixed: '#001d37'
  on-primary-fixed-variant: '#00497e'
  secondary-fixed: '#dde2f3'
  secondary-fixed-dim: '#c1c6d7'
  on-secondary-fixed: '#161c27'
  on-secondary-fixed-variant: '#414754'
  tertiary-fixed: '#d9e3f9'
  tertiary-fixed-dim: '#bdc7dc'
  on-tertiary-fixed: '#121c2c'
  on-tertiary-fixed-variant: '#3d4759'
  background: '#111317'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
typography:
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  container-margin: 2rem
  stack-gap: 1.5rem
  inline-gap: 0.75rem
  section-padding: 1.25rem
  input-padding: 0.75rem 1rem
---

## Brand & Style

The design system embodies a **Corporate / Modern** aesthetic with a focus on high-density information display and executive-level clarity. It leverages a deep, dark theme to minimize eye strain during prolonged analysis while utilizing sharp, subtle borders to maintain structure without visual noise. 

The emotional response is one of **authority, precision, and intelligence**. The UI stays out of the way of the data, using whitespace efficiently to separate distinct executive events while maintaining a cohesive dashboard experience.

## Colors

The palette is built on a foundation of "Obsidian" neutrals. The background uses a deep black-gray to provide maximum contrast for white and blue elements. 

- **Primary:** An "Electric Blue" used for interactive elements and highlights.
- **Surface Tiers:** Backgrounds transition from `#0f1115` (base) to `#1a202c` (cards) and `#2d3748` (inputs).
- **Functional States:** Success and Information states are unified under the blue spectrum, reflecting the "Feedback" highlights seen in the reference. Success uses a vibrant blue text, while Info/Banner states use a muted blue wash (`#2a4365`) for background containment.

## Typography

The design system utilizes **Hanken Grotesk** for its sharp, contemporary feel and excellent legibility in high-density data environments. 

- **Headlines:** Bold and impactful, used to delineate major sections and company names.
- **Meta-data:** Smaller, secondary information (dates, timestamps) uses `body-sm` with a reduced opacity (approx 70%) to maintain hierarchy.
- **Labels:** Used for form headers and button text, ensuring clear actionable instructions.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for the central content well to ensure readability on wide monitors, typical of executive workstations. 

- **Vertical Rhythm:** Elements are stacked with consistent gaps (24px) to separate distinct "Events."
- **Sidebars:** A narrow, fixed-width sidebar on the left handles global navigation and view switching.
- **Density:** The system favors a medium-high density, allowing multiple data entries to be visible at once without overwhelming the user.

## Elevation & Depth

This design system avoids heavy shadows, instead relying on **Tonal Layers** and **Subtle Outlines** to create depth.

- **Surface Tiers:** The base layer is the darkest. Cards and interactive sections are slightly lighter to appear "raised."
- **Borders:** All containers and cards use a 1px solid border (`#2d3748`) to define boundaries clearly against the dark background.
- **Active State:** The blue "Feedback" banner uses a solid color fill with no shadow to maintain a flat, modern aesthetic.

## Shapes

The shape language is **Soft** but disciplined. 

- **Cards & Inputs:** Use a 0.25rem (4px) radius to provide a professional, organized look.
- **Interactive Elements:** Buttons and dropdowns follow the same 4px rounding to maintain consistency across the form-heavy interface.
- **Feedback Banners:** These use the same radius to fit perfectly within the card structure.

## Components

### Buttons
Primary actions ("Guardar feedback") use a dark surface with a subtle border and white text. On hover, the border brightens.

### Input Fields & Textareas
Inputs use a darker background than the card surface to create an "inset" feel. Labels are placed directly above the field in a bold, smaller font size.

### Feedback Banners
These are high-visibility status indicators. They feature a desaturated blue background with a bright blue text highlight, containing "Estado vigente" and timestamp information.

### Expandable Sections
"Ver artículos y detalle" uses a chevron icon and a full-width subtle border to indicate interactivity. These sections collapse to save vertical space.

### Status Chips
Discrete tags used within lists to show candidate quality or event priority, utilizing the primary blue color for positive indicators.