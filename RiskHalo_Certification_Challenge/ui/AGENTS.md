Build a production-ready frontend UI for my project RiskHalo using ReactJS + JavaScript (not TypeScript).

The frontend code must go inside a new folder:

/ui

Use modern React (functional components + hooks). Use Vite for setup.

🎯 PROJECT CONTEXT

Backend already exists and provides:

POST /upload → accepts weekly trade Excel file + risk_per_trade

POST /ask → accepts question and returns streaming LLM response

Responses are JSON

Streaming should be handled via Server-Sent Events (SSE) or fetch streaming

Your job is to build a beautiful, professional trading-style frontend and connect it end-to-end with backend APIs.

🧱 REQUIRED FEATURES
1️⃣ File Upload

Trader must be able to:

Upload weekly trade file (.xlsx)

Define risk per trade (number input)

Click "Analyze Session"

Send both file and risk_per_trade to backend /upload endpoint using FormData.

Show:

Success message on upload

Error handling if upload fails

Loading spinner while uploading

2️⃣ Risk Per Trade

Numeric input field

Persist value in localStorage

Automatically populate on reload

Use it when uploading file

3️⃣ ChatGPT-Style Chat Interface

Below the upload section:

Clean chat window

User messages on right

LLM responses on left

Auto-scroll to latest message

Input box at bottom

Send button

4️⃣ Streaming LLM Response

When user asks a question:

Call /ask endpoint

Handle streaming response

Append text as it streams

Do NOT wait for full completion

Smooth real-time streaming display

5️⃣ Thinking Animation

When LLM is generating:

Show:

🤖 Thinking...
📊 Analyzing behavioral patterns...

Add subtle animated dots effect.

Hide when streaming starts.

6️⃣ Page Title Styling

At top center:

RISKHALO (bold, capital)

Design requirement:

“R” in RISK larger font size

“H” in HALO larger font size

“RISK” one color (deep red or gradient red)

“HALO” another color (electric blue or cyan)

Modern, bold trading font

Make it premium and powerful.

7️⃣ Background Design

Make it feel like a professional trading application.

Requirements:

Dark theme

Subtle gradient background (deep navy → black)

Soft glowing grid overlay

Slight animated financial chart line in background (CSS or canvas)

Glassmorphism cards for UI containers

Clean shadows

Smooth transitions

Should resemble professional trading dashboards like tradl.in.

8️⃣ UX Improvements (Be Creative)

Add:

Smooth hover animations

Subtle glow on active input

Rounded corners

Clean card sections:

Upload Panel

Chat Panel

Responsive design (desktop first)

Sticky chat input at bottom

9️⃣ Folder Structure

Create:

/ui
  ├── index.html
  ├── package.json
  ├── vite.config.js
  ├── src/
  │     ├── main.jsx
  │     ├── App.jsx
  │     ├── components/
  │     │       ├── Header.jsx
  │     │       ├── UploadPanel.jsx
  │     │       ├── ChatWindow.jsx
  │     │       ├── ChatMessage.jsx
  │     │       ├── ChatInput.jsx
  │     │       └── ThinkingIndicator.jsx
  │     ├── services/
  │     │       └── api.js
  │     └── styles/
  │             └── global.css
🔌 Backend Integration

In /services/api.js:

Create functions:

uploadSession(file, riskPerTrade)

askQuestion(question, onStreamChunk)

Use fetch API.

Streaming should use:

response.body.getReader()

Parse text chunks and update UI progressively.

Base URL should be configurable via:

const API_BASE = "http://localhost:8000"
🎨 Design System

Color palette:

Deep Navy: #0B1120

Electric Blue: #00C2FF

Risk Red: #FF3B3B

Neon Cyan Glow: #00FFE0

Soft Gray Text: #AAB4C5

Fonts:

Use Google Font: "Orbitron" for title

Use "Inter" for body text

Add smooth animations (CSS transitions).

🧠 Clean Code Rules

Use React hooks

Use useState and useEffect properly

Keep components modular

No unnecessary libraries

No TypeScript

Use pure CSS (no Tailwind)

Clean readable code

🚀 Final Deliverable

Fully working React frontend

Clean professional trading UI

File upload connected to backend

Streaming LLM chat connected

Thinking animation

Responsive layout

Beautiful dark trading aesthetic

Generate all required files with full code.

Do NOT skip implementation details.

This must work end-to-end with backend.