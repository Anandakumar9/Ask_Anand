# 🎨 UI Design Guide - Instacart Style
## StudyPulse - Clean, Modern Design Inspired by Instacart

---

## 🎯 Design Inspiration

**Instacart Design Principles We're Adopting:**
- Clean, white/light backgrounds
- Green (#43B02A) as primary accent color
- Card-based layouts with soft shadows
- Friendly, approachable typography
- Generous white space
- Horizontal scrolling sections
- Clear visual hierarchy
- Subtle animations and micro-interactions

---

## 🎨 Color Palette

### Primary Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Instacart Green** | `#43B02A` | Primary buttons, accents, success states |
| **Dark Green** | `#2D8A1E` | Hover states, emphasis |
| **Light Green** | `#E8F5E3` | Backgrounds, highlights |

### Neutral Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **White** | `#FFFFFF` | Main background |
| **Light Grey** | `#F7F7F7` | Section backgrounds |
| **Medium Grey** | `#767676` | Secondary text |
| **Dark Grey** | `#343538` | Primary text, headings |
| **Border Grey** | `#E8E8E8` | Card borders, dividers |

### Semantic Colors
| Color | Hex | Usage |
|-------|-----|-------|
| **Success** | `#43B02A` | Correct answers, achievements |
| **Warning** | `#FFA500` | Streaks, attention |
| **Error** | `#D63B30` | Wrong answers, errors |
| **Info** | `#0066CC` | Links, information |

---

## 📝 Typography

### Font Family
- **Primary**: SF Pro Display / Inter
- **Fallback**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto

### Type Scale
| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| **H1 - Page Title** | 28px | Bold (700) | 34px |
| **H2 - Section Header** | 20px | SemiBold (600) | 26px |
| **H3 - Card Title** | 16px | SemiBold (600) | 22px |
| **Body Large** | 16px | Regular (400) | 24px |
| **Body** | 14px | Regular (400) | 20px |
| **Caption** | 12px | Regular (400) | 16px |
| **Button** | 16px | SemiBold (600) | 20px |

---

## 📐 Spacing System

Using 4px base unit:
- `xs`: 4px
- `sm`: 8px
- `md`: 16px
- `lg`: 24px
- `xl`: 32px
- `xxl`: 48px

### Component Spacing
- Card padding: 16px
- Section gap: 24px
- List item gap: 12px
- Button padding: 16px 24px

---

## 🃏 Card Components

### Standard Card
```css
.card {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 16px;
  border: 1px solid #E8E8E8;
}
```

### Highlighted Card (Continue Studying)
```css
.card-highlight {
  background: linear-gradient(135deg, #43B02A 0%, #2D8A1E 100%);
  color: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(67, 176, 42, 0.3);
}
```

### Selection Card (Exam/Subject)
```css
.card-selectable {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 16px;
  border: 2px solid #E8E8E8;
  transition: all 0.2s ease;
}

.card-selectable:hover {
  border-color: #43B02A;
  box-shadow: 0 4px 12px rgba(67, 176, 42, 0.15);
}

.card-selectable.selected {
  border-color: #43B02A;
  background: #E8F5E3;
}
```

---

## 🔘 Button Styles

### Primary Button (Green)
```css
.btn-primary {
  background: #43B02A;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px 24px;
  font-weight: 600;
  font-size: 16px;
  transition: background 0.2s ease;
}

.btn-primary:hover {
  background: #2D8A1E;
}

.btn-primary:disabled {
  background: #E8E8E8;
  color: #767676;
}
```

### Secondary Button (Outlined)
```css
.btn-secondary {
  background: white;
  color: #343538;
  border: 1px solid #E8E8E8;
  border-radius: 12px;
  padding: 16px 24px;
  font-weight: 600;
}

.btn-secondary:hover {
  border-color: #43B02A;
  color: #43B02A;
}
```

### Text Button
```css
.btn-text {
  background: transparent;
  color: #43B02A;
  font-weight: 600;
  padding: 8px 16px;
}
```

---

## 📱 Screen Layouts

### Screen 1: Home Dashboard
```
┌─────────────────────────────────────┐
│  Good Morning, Anand! 👋    [👤]   │  ← Greeting + Avatar
├─────────────────────────────────────┤
│  🔍 Search exams, subjects...       │  ← Search Bar
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ 🟢 Continue where you left  │   │  ← Green Banner Card
│  │    History of AP    60%     │   │
│  │              [Resume]       │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  Your Exams                        │
│  ┌──────┐ ┌──────┐ ┌──────┐       │  ← Horizontal Scroll
│  │ UPSC │ │ SSC  │ │ Bank │ → → → │
│  │      │ │      │ │      │       │
│  └──────┘ └──────┘ └──────┘       │
├─────────────────────────────────────┤
│  Popular Subjects                   │
│  ┌──────────┐ ┌──────────┐        │
│  │ 🌍 Geo   │ │ 📚 His   │        │  ← 2x2 Grid
│  └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐        │
│  │ 🏛️ Polity│ │ 📈 Eco   │        │
│  └──────────┘ └──────────┘        │
├─────────────────────────────────────┤
│  🏠    📖    📝    📊    👤       │  ← Bottom Nav
│  Home  Study Tests Progress Profile │
└─────────────────────────────────────┘
```

### Screen 2: Exam Selection
```
┌─────────────────────────────────────┐
│  ←  Select Your Exam        Skip   │  ← Header
├─────────────────────────────────────┤
│  🔍 Search exams...                 │  ← Search
├─────────────────────────────────────┤
│  Government Exams                   │  ← Category Label
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │ UPSC │ │ SSC  │ │ Bank │ → → → │  ← Cards
│  │100+  │ │ 80+  │ │ 60+  │       │
│  └──────┘ └──────┘ └──────┘       │
├─────────────────────────────────────┤
│  Engineering Exams                  │
│  ┌──────┐ ┌──────┐                 │
│  │ JEE  │ │ GATE │ → → →          │
│  └──────┘ └──────┘                 │
├─────────────────────────────────────┤
│  School Boards                      │
│  ┌──────┐ ┌──────┐                 │
│  │CBSE10│ │CBSE12│                 │
│  └──────┘ └──────┘                 │
├─────────────────────────────────────┤
│         [ Continue ]               │  ← Primary Button
└─────────────────────────────────────┘
```

### Screen 3: Study Timer
```
┌─────────────────────────────────────┐
│  ←  Study Session          ⋮       │
├─────────────────────────────────────┤
│  UPSC > Geography > Rivers          │  ← Breadcrumb Pills
├─────────────────────────────────────┤
│                                     │
│           ┌─────────┐              │
│          │   45:00  │              │  ← Large Timer
│          │   mins   │              │
│           └─────────┘              │
│                                     │
├─────────────────────────────────────┤
│   [Pause]  [End]  [Focus]          │  ← Control Buttons
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ 🎯 Session Goal             │   │
│  │ Complete 45 min of study    │   │
│  │ ✓ You're doing great!       │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  📝 Add a quick note...            │
└─────────────────────────────────────┘
```

### Screen 4: Mock Test Question
```
┌─────────────────────────────────────┐
│  Question 5 of 15        ⏱️ 08:32  │
├─────────────────────────────────────┤
│  ████████████░░░░░░░░░░░░░  33%    │  ← Progress Bar
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ 📅 Previous Year 2022       │   │
│  │                             │   │
│  │ Which river is known as the │   │
│  │ 'Sorrow of Bengal'?         │   │  ← Question Card
│  │                        🔖  │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  ○  (A) Ganga                      │
│  ○  (B) Brahmaputra                │
│  ●  (C) Damodar          ✓        │  ← Selected (green)
│  ○  (D) Hooghly                    │
├─────────────────────────────────────┤
│  ☐ Mark for Review                 │
├─────────────────────────────────────┤
│   [Previous]  ●●●○○  [  Next  ]    │
└─────────────────────────────────────┘
```

### Screen 5: Test Results
```
┌─────────────────────────────────────┐
│  ✕  Test Results            🔗     │
├─────────────────────────────────────┤
│                                     │
│           ✓  🎉                    │
│                                     │
│     Congratulations!               │  ← Success State
│     You earned a star! ⭐          │
│                                     │
│          92%                       │  ← Large Score
│       Your Score                   │
│                                     │
├─────────────────────────────────────┤
│  ✓ 12 Correct   ✕ 3 Wrong  ⏱️ 18m │  ← Stats Pills
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐   │
│  │ Performance Analysis        │   │
│  │                             │   │
│  │ Accuracy   ████████░░  92% │   │
│  │ Speed      ██████████  Good│   │
│  │ Consistent ███████░░░  85% │   │
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│      [ View Answers ]              │
│      Rate Questions                │
│      [ Back to Home ]              │  ← Green Button
└─────────────────────────────────────┘
```

---

## 🎬 Animations & Transitions

### Micro-interactions
| Element | Animation | Duration |
|---------|-----------|----------|
| Button tap | Scale 0.97 | 100ms |
| Card hover | Elevation + border | 200ms |
| Page transition | Slide right/left | 300ms |
| Progress bar | Smooth fill | 400ms |
| Star earned | Bounce + sparkle | 600ms |
| Success check | Draw SVG path | 500ms |

### Loading States
- Skeleton screens with subtle shimmer
- Spinner: Green circular with 1s rotation
- Pull-to-refresh: Green indicator

---

## 📱 Bottom Navigation

```css
.bottom-nav {
  background: white;
  border-top: 1px solid #E8E8E8;
  padding: 8px 0;
  display: flex;
  justify-content: space-around;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #767676;
  font-size: 10px;
}

.nav-item.active {
  color: #43B02A;
}

.nav-item .icon {
  font-size: 24px;
  margin-bottom: 4px;
}
```

---

## ✅ Design Checklist

- [x] White/light backgrounds for clean look
- [x] Green (#43B02A) as primary accent
- [x] Soft shadows on cards (no harsh edges)
- [x] 12-16px border radius throughout
- [x] Generous padding and white space
- [x] Clear typography hierarchy
- [x] Horizontal scrolling for categories
- [x] Friendly, approachable tone
- [x] Progress indicators everywhere
- [x] Celebration animations for achievements

---

## 🔧 CSS Variables

```css
:root {
  /* Colors */
  --color-primary: #43B02A;
  --color-primary-dark: #2D8A1E;
  --color-primary-light: #E8F5E3;
  --color-text-primary: #343538;
  --color-text-secondary: #767676;
  --color-background: #FFFFFF;
  --color-background-secondary: #F7F7F7;
  --color-border: #E8E8E8;
  --color-error: #D63B30;
  --color-warning: #FFA500;
  
  /* Spacing */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  
  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
  
  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

---

*Design Version: 2.0 - Instacart Inspired | January 26, 2026*
