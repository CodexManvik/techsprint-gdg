# Interview Mirror Frontend

Production-ready React frontend for the Interview Mirror AI coaching platform.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development Server

The app will run on `http://localhost:5173`

## Backend Connection

The frontend expects the FastAPI backend to be running on `http://localhost:8000`

Make sure the backend WebSocket endpoint is available at `ws://localhost:8000/ws`

## Tech Stack

- React 18+ with TypeScript
- Vite for build tooling
- Tailwind CSS v4 for styling
- Zustand for state management
- React Router v6 for routing
- Framer Motion for animations
- Recharts for data visualization
- Lucide React for icons

## Project Structure

```
src/
├── components/
│   ├── dashboard/     # Report charts and metrics
│   ├── interview/     # Interview session UI
│   ├── lobby/         # Setup wizard components
│   ├── ui/            # Reusable UI primitives
│   └── shared/        # Shared components
├── hooks/             # Custom React hooks
├── stores/            # Zustand state management
├── lib/               # Utility functions
├── pages/             # Route pages
└── App.tsx            # Main app component
```

## Features

- Light mode professional UI
- Real-time WebSocket communication
- Camera and microphone integration
- Live posture and stress monitoring
- AI-powered feedback system
- Comprehensive interview reports
- Responsive design
