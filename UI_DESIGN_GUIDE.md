# 🎨 UI Design Guide
## StudyPulse - Visual Design Documentation

---

## 📱 Screen Overview

This document contains the visual design for all major screens of the StudyPulse application.

---

## 🎨 Design System

### Color Palette

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| **Primary Purple** | `#7C3AED` | Primary actions, accents |
| **Secondary Blue** | `#3B82F6` | Secondary elements |
| **Dark Background** | `#0F0A1E` | Main background |
| **Card Background** | `rgba(255,255,255,0.05)` | Glassmorphism cards |
| **Success Gold** | `#F59E0B` | Stars, achievements |
| **Text Primary** | `#FFFFFF` | Headings, important text |
| **Text Secondary** | `#9CA3AF` | Descriptions, hints |

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| **App Title** | Inter | 24px | Bold (700) |
| **Screen Heading** | Inter | 20px | SemiBold (600) |
| **Card Title** | Inter | 16px | Medium (500) |
| **Body Text** | Inter | 14px | Regular (400) |
| **Caption** | Inter | 12px | Regular (400) |
| **Timer Display** | Inter | 64px | Bold (700) |

### Design Principles

1. **Glassmorphism** - Frosted glass effect with subtle blur
2. **Neon Glow** - Purple/blue glow on interactive elements
3. **Gradient Accents** - Purple-to-blue gradients on buttons
4. **Smooth Corners** - 16px border radius on all cards
5. **Subtle Animations** - Micro-interactions on all buttons
6. **Dark Theme** - Easy on eyes for long study sessions

---

## 📱 Screen 1: Exam Selection (Onboarding)

### Description
The first step of the study setup wizard where users select their target exam.

### Key Elements
- **Progress Indicator**: Shows 3 steps (Exam → Subject → Topic)
- **Search Bar**: Quick filter for exams
- **Exam Cards**: Grid layout with icons
- **Selected State**: Purple glow border on selected card
- **Navigation Hints**: Shows next steps at bottom

### User Flow
```
User opens app → Select Exam → Select Subject → Select Topic
```

### Interactions
- Tap card to select (shows glow effect)
- Search filters results in real-time
- "Next" button appears when selection made

---

## 📱 Screen 2: Study Timer

### Description
Focused study session timer with distraction-free design.

### Key Elements
- **Circular Timer**: Large, centered with gradient ring
- **Topic Info**: Current topic and exam displayed
- **Control Buttons**: Pause, Stop, Focus Mode
- **Motivational Text**: Encouraging message
- **Session Info**: Duration card at bottom

### Timer States
| State | Visual |
|-------|--------|
| Running | Ring animates, purple glow |
| Paused | Ring static, button changes to Play |
| Complete | Ring full, celebration animation |

### Interactions
- Tap Pause to pause/resume
- Tap Stop to end session early
- Focus Mode dims notifications

---

## 📱 Screen 3: Mock Test Question

### Description
The main test-taking interface where users answer questions.

### Key Elements
- **Question Counter**: "Q 5/15" format
- **Timer**: Real-time countdown
- **Progress Bar**: Visual question progress
- **Question Card**: Glassmorphism with question text
- **AI Badge**: Shows if question is AI-generated
- **Options**: 4 choices with selection state
- **Navigation**: Previous/Next buttons + grid

### Option States
| State | Visual |
|-------|--------|
| Default | Dark card, subtle border |
| Hover | Slight glow |
| Selected | Purple border + glow |
| Correct (review) | Green border |
| Incorrect (review) | Red border |

### Interactions
- Tap option to select (only one allowed)
- Star icon to mark for review
- Grid opens question navigator
- Previous/Next for navigation

---

## 📱 Screen 4: Test Results (Success)

### Description
Celebratory results screen shown when scoring ≥85%.

### Key Elements
- **Confetti Animation**: Celebration effect
- **Star Badge**: Golden star with glow
- **Score Display**: Large percentage
- **Stats Row**: Correct count, time, stars
- **Performance Cards**: Accuracy, Speed, Consistency
- **Action Buttons**: Analysis, Rate, Dashboard

### Result Variations
| Score | Visual |
|-------|--------|
| ≥85% | Gold star, confetti, "Congratulations!" |
| 70-84% | Silver badge, "Good job!" |
| <70% | Encouragement, "Keep practicing!" |

---

## 📱 Screen 5: Dashboard Home

### Description
Main dashboard showing user progress and quick actions.

### Key Elements
- **Profile Section**: Avatar, greeting, notifications
- **Stats Row**: Stars, Avg Score, Streak
- **Continue Card**: Resume last session
- **Quick Actions**: 4 primary actions grid
- **Recent Activity**: List of past sessions
- **Bottom Nav**: Home, Study, Tests, Profile

### Dashboard Widgets
| Widget | Content |
|--------|---------|
| Stars | Total stars earned |
| Avg Score | Rolling average across tests |
| Streak | Consecutive study days |
| Continue | Last incomplete topic |

---

## 🔄 User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE USER FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   App Open   │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
     ┌────────▼────────┐       ┌────────▼────────┐
     │  New User?      │       │  Returning      │
     │  → Onboarding   │       │  → Dashboard    │
     └────────┬────────┘       └────────┬────────┘
              │                         │
              │                         │
              ▼                         ▼
     ┌─────────────────────────────────────────────┐
     │              STUDY SETUP WIZARD              │
     │  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
     │  │ Screen 1│→ │ Subject │→ │  Topic  │     │
     │  │ (Exam)  │  │ Select  │  │ Select  │     │
     │  └─────────┘  └─────────┘  └─────────┘     │
     └────────────────────┬────────────────────────┘
                          │
                          ▼
     ┌─────────────────────────────────────────────┐
     │              SCREEN 2: STUDY TIMER           │
     │  • User studies for selected duration        │
     │  • Timer counts down                         │
     │  • Can pause/resume/stop                     │
     └────────────────────┬────────────────────────┘
                          │ Timer Complete
                          ▼
     ┌─────────────────────────────────────────────┐
     │              SCREEN 3: MOCK TEST             │
     │  • 50% Previous Year + 50% AI Questions      │
     │  • Answer each question                      │
     │  • Navigate with Previous/Next               │
     │  • Submit when done                          │
     └────────────────────┬────────────────────────┘
                          │ Submit
                          ▼
     ┌─────────────────────────────────────────────┐
     │              SCREEN 4: RESULTS               │
     │  • Score calculated                          │
     │  • Star awarded if ≥85%                      │
     │  • Rate AI questions                         │
     │  • View detailed analysis                    │
     └────────────────────┬────────────────────────┘
                          │
                          ▼
     ┌─────────────────────────────────────────────┐
     │              SCREEN 5: DASHBOARD             │
     │  • Updated stars count                       │
     │  • New activity logged                       │
     │  • Ready for next session                    │
     └─────────────────────────────────────────────┘
```

---

## 📐 Responsive Breakpoints

| Device | Width | Adjustments |
|--------|-------|-------------|
| Mobile S | 320px | Compact cards, smaller fonts |
| Mobile M | 375px | Default design |
| Mobile L | 425px | Slightly larger touch targets |
| Tablet | 768px | 2-column layout where applicable |
| Desktop | 1024px+ | Sidebar navigation, 3-column |

---

## 🎭 Animation Guidelines

| Element | Animation | Duration |
|---------|-----------|----------|
| Page Transition | Slide + Fade | 300ms |
| Button Press | Scale 0.95 | 100ms |
| Card Hover | Glow intensity | 200ms |
| Timer Progress | Smooth decrement | 1000ms |
| Confetti | Particle burst | 2000ms |
| Star Award | Scale bounce | 500ms |

---

## ✅ Design Checklist

- [x] Dark theme for reduced eye strain
- [x] High contrast for accessibility (4.5:1 minimum)
- [x] Large touch targets (44px minimum)
- [x] Clear visual hierarchy
- [x] Consistent spacing (8px grid)
- [x] Loading states for all async operations
- [x] Error states with clear messaging
- [x] Empty states with helpful prompts

---

*Design Version: 1.0 | Last Updated: January 26, 2026*
