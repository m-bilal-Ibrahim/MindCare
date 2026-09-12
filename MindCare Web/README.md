# MindCare Web — FYP Frontend

> React + Vite + Tailwind CSS · Clean Architecture · Ready for backend integration

---

## 📂 Folder Structure

```
src/
├── components/
│   ├── common/          # Reusable atoms: Button, Logo, Badge
│   ├── layout/          # Navbar, Footer
│   ├── sections/        # Landing page sections (Hero, Partners, HowItWorks…)
│   ├── onboarding/      # Role picker cards & header
│   └── mockup/          # PhoneMockup, QRCode visuals
├── constants/           # App-wide constants, nav items, dummy data
├── hooks/               # Custom React hooks (useOnboarding, useScrollPosition)
├── pages/               # Full page components (one per route)
├── router/              # React Router v6 setup
├── services/            # API service layer (swap dummies for real calls)
├── types/               # TypeScript domain types
└── utils/               # Utility functions (cn, etc.)
```

---

## 🖥 Screens

| # | Route | Description |
|---|-------|-------------|
| 1 | `/` | Landing page — hero, how it works, features |
| 2 | `/get-started` | Role picker — client or clinician |
| 3 | `/get-started/client` | Client app download screen |
| — | `/get-started/clinician` | Clinician application form |
| — | `/sign-in` | Secure sign-in page |

---

## 🔌 Backend Integration

All API calls are in `src/services/api.service.ts`.  
Each function has a `TODO` comment showing the real endpoint to uncomment.  
Set your API URL in `.env`:

```
VITE_API_BASE_URL=https://api.mindcare.pk/v1
```

---

## 🔒 Security

- Input validation (client-side) on all forms
- `httpOnly` cookie support via `credentials: 'include'`
- `sessionStorage` token (swap to httpOnly cookie when backend is ready)
- ARIA roles and keyboard navigation throughout
- HIPAA-aligned UX language

---

## 🚀 Run locally

```bash
npm install
npm run dev
```

## 🏗 Build

```bash
npm run build
```

---

## 🌿 Git Branches (planned)

- `feature/screen-1-landing`
- `feature/screen-2-onboarding`
- `feature/screen-3-client-app`
- `feature/auth`
- `feature/clinician-portal`

Push each screen to its own branch in `MindCare Web/` folder on GitHub.
