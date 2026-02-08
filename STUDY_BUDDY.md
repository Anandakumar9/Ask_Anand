You are an AI software architect and prototype builder.

Follow this PRD strictly.
Do not add new features, assumptions, monetization, or platforms.
If something is unclear, ask questions instead of guessing.

---

# 📄 PRODUCT REQUIREMENTS DOCUMENT (PRD)

## AI-BACKED STUDY → TIMER → MOCK TEST APPLICATION

---

## 0. DOCUMENT PURPOSE

This document defines **exact, non-ambiguous product requirements** for building a prototype of a mobile application that helps students **retain studied topics by immediately testing them** using **previous year questions and AI-generated questions via RAG**.

This PRD is written to be:

* Read and executed by an AI (Claude) for prototyping
* Used by a beginner founder with no coding background
* Strictly limited to ideas discussed in this conversation
* Free from assumptions or hallucinated features

---

## 1. PRODUCT VISION (CONFIRMED)

The application helps students:

* Study a topic for a fixed time
* Immediately take a mock test
* Measure retention
* Repeat study if performance is weak

The application enforces a **study → test → feedback loop**.

---

## 2. TARGET USERS (CONFIRMED)

* Students preparing for competitive exams
* Initial example exam used throughout: **UPSC**
* Language: **English only**
* Platform goal: **Native mobile app (Android/iOS)**

---

## 3. CORE PROBLEM (CONFIRMED)

* Students forget what they study
* Students do not test themselves immediately
* Previous year questions are scattered
* Mock tests are not topic-specific or instant
* No feedback loop exists between studying and testing

---

## 4. HIGH-LEVEL PRODUCT FLOW (CONFIRMED)

```
Open App
→ Select Exam
→ Select Subject
→ Select Topic
→ Select Study Timer
→ Study with Timer Running
→ Timer Ends
→ Start Mock Test
→ Answer Questions
→ Evaluation
→ Feedback (Star / Retry)
```

---

## 5. PLATFORM CONSTRAINTS (CONFIRMED)

* MVP is **FREE**
* Rapid prototype required
* English only
* Data already exists (previous year questions / study material)
* No live PDF upload by users during study
* AI/RAG should be **ready before test starts**

---

## 6. USER FLOW — DETAILED, SCREEN BY SCREEN

### 6.1 App Entry

* App opens to a simple welcome screen
* CTA: “Start Study Session”

---

### 6.2 Exam Selection Screen

* Question shown:
  “Which exam are you preparing for?”
* Example option enabled:

  * UPSC
* Only one exam selectable

**State stored:**

```
exam
```

---

### 6.3 Subject Selection Screen

* Question:
  “Which subject are you studying today?”
* Example subjects:

  * Polity
  * Geography
  * History
  * Economy
* One subject selectable

**State stored:**

```
subject
```

---

### 6.4 Topic Selection Screen

* User selects or types topic name
* Example:
  “Fundamental Rights”
* Topic determines which data is retrieved

**State stored:**

```
topic
```

---

### 6.5 Study Timer Selection Screen

* User selects study duration
* Example durations:

  * 15 minutes
  * 30 minutes
  * 45 minutes
  * Custom
* User clicks “Start Study Session”

**State stored:**

```
study_duration
```

---

### 6.6 Active Study Timer Screen (CRITICAL)

* Countdown timer displayed prominently
* Topic name shown
* No distractions
* User is expected to study externally (book/notes)

**IMPORTANT BACKGROUND BEHAVIOR (CONFIRMED):**
While the timer is running:

* The system prepares the mock test
* RAG retrieval runs in the background
* MCQs are prepared or cached
* No user waiting after timer ends

---

### 6.7 Test Ready Screen

* Triggered when timer ends
* Message:
  “Time’s up. Ready to test?”
* Button:
  “Start Mock Test”

---

### 6.8 Mock Test Screen

* MCQs shown one by one
* Each question has:

  * Question text
  * 4 options
* Navigation:

  * Next question
* Progress indicator:
  “Question X of N”
* No back navigation

---

### 6.9 Result & Feedback Screen

* Score shown as percentage
* Logic:

  * ≥ 85% → Star awarded
  * 70%–84% → Normal feedback
  * < 70% → Suggest study again
* Buttons:

  * Retake Test
  * Start New Session

---

## 7. MOCK TEST LOGIC (CONFIRMED)

### 7.1 Question Sources

Each mock test contains:

* Previous year questions (authorized / historical)
* AI-generated questions

Default ratio:

```
50% previous year
50% AI-generated
```

Ratio may be configurable later, but **not required for MVP**.

---

### 7.2 Randomization

* Questions must be randomly selected
* Repeated attempts should not show identical sequences if possible

---

## 8. AI / RAG REQUIREMENTS (CONFIRMED)

### 8.1 Data Source

* Data already exists
* Includes:

  * Previous year questions
  * Study material
* Data is pre-processed before users access the app

---

### 8.2 RAG Behavior

* When topic is selected:

  * Retrieve relevant chunks from vector store
* Retrieval happens **before mock test starts**
* No real-time embedding during user session

---

### 8.3 AI Question Generation

* AI generates MCQs based on:

  * Retrieved context
  * Previous year question patterns
* Questions must:

  * Match exam style
  * Avoid direct copying
  * Be factually accurate

---

### 8.4 User Feedback Loop (CONFIRMED)

* Users can rate AI-generated questions
* Ratings are stored for future validation
* Institutional validation is planned but **not required for MVP**

---

## 9. TIMER + BACKGROUND EXECUTION LOGIC (CONFIRMED)

### 9.1 When Timer Starts

* Trigger background RAG preparation
* Fetch context
* Prepare MCQs
* Cache results

### 9.2 When Timer Ends

* Test is immediately available
* No loading or waiting screen

---

## 10. MCQ CACHING STRATEGY (CONFIRMED)

* Cache MCQs per session
* Cache lifetime:

  * Until test is completed
* On retry:

  * Either reuse cached questions
  * Or regenerate (implementation choice)

Example cache structure:

```
session_id
topic
questions[]
timestamp
```

---

## 11. SCORING & FEEDBACK LOGIC (CONFIRMED)

```
if score >= 85%:
    award_star = true
elif score < 70%:
    suggest_study_again = true
else:
    normal_feedback = true
```

Stars indicate:

* High focus
* High retention
* Eligibility for future benefits (mentorship planned later)

---

## 12. NON-FUNCTIONAL REQUIREMENTS

* Low latency after timer ends
* Predictable AI output (structured MCQs)
* Simple UI
* Beginner-friendly architecture
* Scalable to other exams later

---

## 13. OUT OF SCOPE (STRICT — DO NOT BUILD)

* Monetization
* Ads
* Native mentorship system
* Multilingual support
* Live PDF upload by users
* Coaching dashboards
* Social features
* Rankings / leaderboards

---

## 14. MVP VALIDATION GOAL (CONFIRMED)

* Test with limited dataset (e.g., school exam or small UPSC subset)
* Validate:

  * User flow
  * Timer usefulness
  * Question quality
  * Retention improvement

---

## 15. FUTURE (MENTIONED BUT NOT REQUIRED NOW)

* Mentorship benefits for high-star users
* Multi-language interface
* Global exams
* Advanced analytics

---

## 16. FINAL INSTRUCTION TO AI (IMPORTANT)

When generating a prototype:

* Follow this PRD exactly
* Do not invent features
* Do not add assumptions
* Ask questions if unclear
* Prefer simple implementations
* Optimize for speed and clarity

---

## END OF PRD

---

Number of questions per mock test:

FIXED = 10 questions

Do not display AI explanations unless explicitly enabled in future versions.

Every mock test attempt must generate a fresh question set.

Offline mode is NOT required

FINAL MVP MOCK TEST RULESET (SUMMARY)
Mock Test:
- Questions: 10
- Type: MCQ
- Sources: 50% historical + 50% AI-generated
- Randomized: Yes
- Explanations: Hidden
- Retake: New questions only
- Offline: Not supported

USER FLOW (LOCKED)
Open App
→ Select Exam (UPSC)
→ Select Subject
→ Select Topic
→ Select Study Timer
→ Timer Runs (background RAG prepares test)
→ Timer Ends
→ Start Mock Test
→ Answer 10 MCQs
→ Score Evaluation
→ Feedback (Star / Retry)

