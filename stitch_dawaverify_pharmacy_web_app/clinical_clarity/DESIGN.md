---
name: Clinical Clarity
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#3d4947'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#6d7a77'
  outline-variant: '#bcc9c6'
  surface-tint: '#006a61'
  primary: '#00685f'
  on-primary: '#ffffff'
  primary-container: '#008378'
  on-primary-container: '#f4fffc'
  inverse-primary: '#6bd8cb'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#006860'
  on-tertiary: '#ffffff'
  tertiary-container: '#248279'
  on-tertiary-container: '#f3fffc'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#89f5e7'
  primary-fixed-dim: '#6bd8cb'
  on-primary-fixed: '#00201d'
  on-primary-fixed-variant: '#005049'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#9cf2e8'
  tertiary-fixed-dim: '#80d5cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#00504a'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Outfit
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Outfit
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  audio-timer:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-tablet: 1.5rem
  gutter-desktop: 2rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: auto
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system establishes an empathetic, uncompromisingly reliable mobile healthcare experience designed to safeguard everyday patients, caregivers, and visually impaired individuals against counterfeit medication. The interface balances high-stakes forensic precision with radical human accessibility. 

The aesthetic is Modern Clinical Humanism: a blend of pristine medical-grade clarity and accessible warmth. Rather than feeling sterile or alarming, the visual atmosphere builds immediate trust and calm during moments of vulnerability. Visual signals must be instantly decodable under adverse physical conditions—such as low lighting in rural dispensaries, shaky hands, or visual impairments.

Key experiential pillars:
- **Instant Assurance**: Immediate visual and auditory confirmation of safety thresholds without medical jargon.
- **Radical Legibility**: High structural contrast, generous touch targets (exceeding 48px baseline), and distinct semantic status signposts.
- **Multimodal Feedback**: Audio-first dosage playback paired with tactile, card-based visual structures.

## Colors

The color palette centers on safety, discernment, and physiological reassurance. High WCAG AAA contrast ratios guide critical interactions to protect all users under variable glare and screen qualities.

- **Primary (`#0D9488`) & Deep Teal (`#0F766E`)**: Anchors primary navigation, active scanning viewfinders, and affirmative actions. Communicates clinical validation and modern digital healthcare expertise.
- **Secondary / Verification Mint (`#10B981`)**: Dedicated exclusively to authenticated medication matches, genuine batch confirmations, and positive dosage completion states. Paired with soft tint `#F0FDF4` for card backdrops.
- **Tertiary / Clinical Slate (`#0F172A`)**: The structural bedrock. Replaces standard grays to provide maximum text readability without harsh pure-black eye fatigue.
- **Alert Amber (`#F59E0B`)**: Signals secondary anomalies such as near-expiry dates, broken seals, packaging redesign advisories, or unverified distributor flags.
- **Counterfeit Crimson (`#EF4444`)**: Reserved strictly for high-severity counterfeit warnings, recalled serial numbers, and direct warnings to halt consumption.
- **Surfaces (`#F8FAFC`, `#F0FDF4`, `#FFFFFF`)**: Sterile, glare-reducing canvases that provide clear elevation layers for floating action panels and audio controls.

## Typography

The type system blends the geometric friendliness of Outfit for display landmarks and verification status banners with the utilitarian precision of Inter for body instructions, medical dosages, and active audio states.

Key guidelines:
- **Headline Rendering**: `Outfit` provides rounded geometric forms that reduce medical stress and visually humanize clinical verification verdicts.
- **Data & Dosage Legibility**: `Inter` handles all micro-copy, warnings, dosage measurements (mg/ml), and batch numbers. Its tall x-height and distinct glyph apertures prevent confusion between characters like `0` and `O`, or `1` and `l`.
- **Accessible Scaling**: Default minimum body size is anchored at 16px (`body-md`) on mobile to eliminate pinch-to-zoom requirements for elder users.
- **Audio-Specific Metrics**: The `audio-timer` token relies on tabular figures to maintain zero layout jitter during live audio speech playback.

## Layout & Spacing

The layout is built mobile-first, targeting an ergonomic one-handed thumb zone for critical actions like starting scans and triggering audio playback.

- **Mobile Canvas**: A continuous 4-column fluid grid bounded by `1rem` (16px) margins. Critical interactive triggers (scanner reticle triggers, audio dosage bars) reside within the bottom 40% of the viewport.
- **Tablet & Large Screens**: Reflows into an 8-column layout with max container bounds of 640px for single-column card flows (to prevent long, fatiguing line lengths for dosage instructions), or 12 columns with split views (live viewfinder beside verification results) on larger displays.
- **Rhythm & Touch Buffer**: Component padding strictly adheres to the 8pt spatial system via `space-sm` (8px), `space-md` (16px), and `space-xl` (32px). All interactable targets must have a minimum physical boundary footprint of 48px by 48px, padded internally using `space-md`.

## Elevation & Depth

Visual hierarchy uses clean, medical-grade tonal layers combined with soft, daylight-tinted ambient shadows. Avoid heavy dropshadows or complex 3D skeuomorphism, prioritizing calm surface separation.

- **Surface 0 (Background)**: Clean `#F8FAFC` base that keeps device screens cool and legible.
- **Surface 1 (Card Level)**: Pure `#FFFFFF` with a 1px structural stroke in `#E2E8F0` and an ambient shadow (`box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.04), 0 2px 6px -1px rgba(15, 23, 42, 0.02)`).
- **Surface 2 (Elevated Audio Pill & Alerts)**: Floating action pills and urgent modal warnings float with higher focal presence (`box-shadow: 0 10px 25px -3px rgba(13, 148, 136, 0.12), 0 4px 10px -2px rgba(15, 23, 42, 0.05)`).
- **Verification States**: Authenticated surfaces employ an ambient halo using a 5% opacity tint of Verification Mint (`#10B981`), signaling authenticity passively across the entire panel perimeter.

## Shapes

The design uses roundedness level `2` (0.5rem base radius, 1rem for `rounded-lg`, and 1.5rem for `rounded-xl`).

- **Base Components & Inputs**: Buttons, text fields, and standard list items use `rounded` (0.5rem / 8px) to retain an authoritative, structured medical feel.
- **Verification & Status Cards**: Result summary containers and alert sections use `rounded-lg` (1rem / 16px) to frame drug data cleanly.
- **Audio Control Shells & Status Badges**: Floating audio dosage players, category tags, and counterfeit indicators use full pill shapes (`rounded-full` / 9999px), providing an ergonomic, tactile affordance that feels soft and touch-ready.

## Components

### Buttons & Scanning Triggers
- **Primary Scan Action**: Full-width or prominent pill button. Height: 56px (accessible touch target). Filled with `#0D9488`, bold white `Outfit` typography, accompanied by a clear camera/barcode icon. Hover/active state deepens to `#0F766E`.
- **Secondary Actions**: Bordered button with a 1.5px border in `#0D9488`, transparent background, text in `#0D9488`.
- **Critical Warning Actions**: Counterfeit state triggers use solid `#EF4444` with white text, providing an unambiguous exit/report flow.

### Status Chips & Badges
- Built as pill shapes with 8px vertical and 16px horizontal padding.
- **Verified Genuine**: `#10B981` text over `#F0FDF4` background with a solid checkmark icon.
- **Counterfeit Suspect**: `#EF4444` text over `#FEF2F2` background with a warning triangle icon.
- **Advisory / Warning**: `#F59E0B` text over `#FFFBEB` background with an alert icon.

### Accessible Audio Dosage Player
- A persistent floating capsule (`rounded-full`) anchored to the bottom of the verification screen.
- Elevated with Surface 2 ambient teal shadow.
- Houses a prominent circular Play/Pause toggle (minimum 48px diameter) in `#0D9488` with white iconography.
- Interactive audio scrub line / dynamic SVG waveform styled in `#10B981` (active) and `#E2E8F0` (unplayed).
- Displays remaining time in bold tabular type (`audio-timer`), alongside a language-selection toggle icon (e.g., switching between local dialects and clear simplified audio).

### Verification Cards
- Stacked card architecture with a white background and subtle borders.
- Top section contains the medication trade name, chemical compound, strength (e.g., "500 mg"), and prominent authentic/fake status indicator.
- Internal metadata list displays batch ID, expiration date, and manufacturer details with high contrast between label (`#64748B`) and value (`#0F172A`).

### Form Inputs & Search Fields
- Minimum height of 52px with a 1.5px border (`#CBD5E1`).
- Active focus displays a crisp 2px outer ring in `#0D9488` with zero layout shift.
- Clear visual error states with a persistent red message text and icon positioned directly beneath the input field.

### Checkboxes & Segmented Controls
- Checkboxes feature a minimum 24px box within a 48px hit area, filling with `#0D9488` upon selection.
- Segmented language and dosage unit selectors use pill containers with a sliding white pill indicator over a `#F1F5F9` background track.