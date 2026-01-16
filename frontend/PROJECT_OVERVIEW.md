# Interview Mirror - Frontend Architecture

## Overview

Production-ready React frontend for Interview Mirror, an AI-powered interview coaching platform. Built with modern web technologies and optimized for performance and user experience.

## Design Philosophy

### Light Mode Professional UI
- **Background**: Porcelain (#F8F9FA) - reduces eye strain
- **Typography**: Dark Slate (#1E293B) - optimal readability
- **Accents**: 
  - Primary Blue (#3B82F6) - trust and professionalism
  - Amber (#F59E0B) - warnings
  - Soft Red (#EF4444) - errors/stress indicators

### Invisible Interface
- Minimal borders and generous whitespace
- Soft diffuse shadows for depth
- Focus on content, not chrome
- Distraction-free interview mode

## Application Flow

### Stage A: Home Screen
**Purpose**: Entry point for new or returning users

**Components**:
- Split action card (New Interview / Continue Session)
- Session ID validation
- Clean, centered hero layout

**User Actions**:
- Start new interview → Navigate to Lobby
- Enter session ID → Validate → Resume session

### Stage B: The Lobby (Setup Wizard)
**Purpose**: Configure interview parameters

**Step 1: Identity**
- Resume upload with drag-and-drop
- PDF validation with friendly error messages
- Server-side text extraction

**Step 2: Context**
- 12 persona cards (Google SRE, Amazon Bar Raiser, etc.)
- Difficulty slider (Junior → Staff+) with color coding
- Multi-select topic chips (System Design, DSA, Behavioral, etc.)

**Step 3: Tech Check**
- Camera/microphone permission verification
- Live video preview
- Visual permission guide if blocked
- Cannot proceed without hardware access

### Stage C: The Interview (Focus Mode)
**Purpose**: Distraction-free interview experience

**Key Features**:
- AI Avatar with audio visualizer (reacts to TTS amplitude)
- Draggable PiP video feed of user
- Status Halo (Blue/Amber/Red border glow)
- Dynamic Island for live feedback
- Bottom control bar (Mute, Text Input, End)

**Real-time Monitoring**:
- Posture tracking
- Stress level detection
- Eye contact measurement
- Speaking pace analysis

### Stage D: The Report Card
**Purpose**: Comprehensive performance analytics

**Sections**:
- Executive Summary (AI-generated)
- Metrics Grid (WPM, Stress, Eye Contact, Posture)
- Radar Chart (User vs Ideal Candidate)
- Integrity Heatmap (Gaze tracking, face detection)

## Technical Architecture

### State Management (Zustand)
```typescript
SessionState {
  - sessionId
  - resumeFile & resumeText
  - selectedPersona
  - difficulty & topics
  - isConnected (WebSocket)
  - statusHalo (blue/amber/red)
  - currentFeedback
  - metrics (posture, stress, eyeContact, wpm)
}
```

### WebSocket Communication
**Endpoint**: `ws://localhost:8000/ws`

**Message Types**:
- `audio`: TTS audio data (base64)
- `metrics`: Real-time performance data
- `feedback`: Live coaching messages
- `question`: New interview question
- `summary`: Final interview summary

### Custom Hooks

**useWebSocket**
- Manages WebSocket connection lifecycle
- Auto-reconnect on disconnect
- Message parsing and routing
- Audio playback handling

**useAudio**
- Microphone access and recording
- Audio level visualization
- Mute/unmute functionality
- Real-time amplitude tracking

**useMediaPipe**
- Camera stream management
- Permission checking
- Video feed control

## Component Architecture

### UI Primitives (`components/ui/`)
- Button (4 variants, 3 sizes)
- Card (with Header, Title, Content)
- Input (styled text input)
- Slider (range input with custom styling)
- Toast (animated notifications)

### Lobby Components (`components/lobby/`)
- ResumeUploader: Drag-and-drop with validation
- PersonaSelector: Grid of interviewer cards
- DifficultySlider: Color-coded range slider
- TopicSelector: Multi-select chips
- TechCheck: Hardware permission verification

### Interview Components (`components/interview/`)
- AudioVisualizer: Canvas-based waveform animation
- VideoFeed: Draggable PiP with expand/collapse
- DynamicIsland: Top notification pill
- ControlBar: Bottom action buttons

### Dashboard Components (`components/dashboard/`)
- RadarChart: Performance comparison visualization
- MetricsGrid: Key performance indicators
- IntegrityHeatmap: Gaze and face detection events

## Performance Optimizations

### Code Splitting
- React vendor bundle (46KB)
- Chart vendor bundle (290KB)
- Animation vendor bundle (118KB)
- Main application bundle (250KB)

### Build Configuration
- TypeScript strict mode enabled
- Tree shaking for unused code
- CSS purging via Tailwind
- Gzip compression (78% reduction)

### Runtime Optimizations
- Lazy loading for routes
- Memoized components
- Debounced WebSocket messages
- RequestAnimationFrame for animations

## Error Handling

### ErrorBoundary
- Catches React component errors
- Displays friendly error UI
- Provides reset functionality
- Logs errors for debugging

### Input Validation
- PDF file type checking
- Session ID format validation
- Required field enforcement
- Natural language error messages

### Network Resilience
- WebSocket auto-reconnect
- API request timeout handling
- Graceful degradation
- Offline state detection

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Focus management
- Color contrast compliance (WCAG AA)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- WebRTC required for camera/mic
- WebSocket support required

## Environment Configuration

### Development
```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_DEV_MODE=true
```

### Production
```bash
VITE_API_URL=https://api.interviewmirror.com
VITE_WS_URL=wss://api.interviewmirror.com/ws
VITE_DEV_MODE=false
```

## API Integration

### REST Endpoints
- `POST /api/upload-resume`: Upload and parse resume
- `GET /api/session/:id`: Retrieve session data
- `GET /api/report`: Fetch interview report
- `POST /api/start-interview`: Initialize interview session

### WebSocket Events
- Client → Server: User responses, control commands
- Server → Client: Questions, feedback, metrics, audio

## Future Enhancements

- Multi-language support
- Dark mode toggle
- Screen recording playback
- Interview scheduling
- Progress tracking dashboard
- Social sharing features
- Mobile responsive design
- PWA capabilities

## Development Workflow

1. Install dependencies: `npm install`
2. Start dev server: `npm run dev`
3. Make changes (hot reload enabled)
4. Run type check: `npm run build`
5. Preview production: `npm run preview`

## Testing Strategy

- Component unit tests (Jest + React Testing Library)
- Integration tests for user flows
- E2E tests for critical paths (Playwright)
- Visual regression tests (Chromatic)
- Performance monitoring (Lighthouse CI)

## Deployment

### Build
```bash
npm run build
```

### Output
- `dist/` directory with optimized assets
- Static files ready for CDN deployment
- Gzipped assets for faster loading

### Hosting Options
- Vercel (recommended)
- Netlify
- AWS S3 + CloudFront
- Azure Static Web Apps
- Google Cloud Storage

## Monitoring

- Error tracking: Sentry
- Analytics: Google Analytics / Plausible
- Performance: Web Vitals
- User feedback: Hotjar / FullStory

## Security Considerations

- No sensitive data in localStorage
- HTTPS only in production
- CSP headers configured
- XSS protection enabled
- CORS properly configured
- Input sanitization
- Rate limiting on API calls

## License

Proprietary - All rights reserved
