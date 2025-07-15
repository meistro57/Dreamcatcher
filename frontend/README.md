# Dreamcatcher Frontend

Mobile-first PWA for instant idea capture. Because inspiration doesn't wait for loading screens.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Features

### Instant Capture
- **Voice Recording**: Hold button to record, release to process
- **Text Input**: Quick text entry with smart suggestions
- **Offline Mode**: Captures work without internet, sync later
- **Emergency Mode**: Skip login for urgent idea capture

### Idea Management
- **Timeline View**: Chronological idea feed with filtering
- **Visual Gallery**: Generated images linked to ideas
- **Proposal Queue**: AI-generated project proposals
- **Search & Filter**: Find ideas by content, tags, or date

### Real-time Updates
- **WebSocket Connection**: Live agent status and notifications
- **Push Notifications**: Alerts for new proposals and insights
- **Background Sync**: Seamless offline-to-online transitions

## Mobile Optimization

### PWA Features
- **Installable**: Add to home screen like native app
- **Offline First**: Core functionality works without connection
- **Fast Loading**: Cached resources and optimized bundles
- **Native Feel**: Smooth animations and gestures

### Voice Interface
- **Wake Word**: "Hey Dreamcatcher" activation
- **Noise Cancellation**: Clear audio in any environment
- **Real-time Transcription**: See words as you speak
- **Voice Shortcuts**: Common commands via speech

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development
- **State Management**: Zustand for simplicity
- **Styling**: Tailwind CSS for rapid UI
- **Audio**: Web Audio API for voice processing
- **PWA**: Workbox for service worker management

## Directory Structure

```
src/
├── components/     # Reusable UI components
├── pages/         # Route components
├── stores/        # State management
├── services/      # API and external services
├── utils/         # Helper functions
├── hooks/         # Custom React hooks
└── assets/        # Static resources
```

## Development

### Available Scripts
```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run preview    # Preview production build
npm run test       # Run unit tests
npm run lint       # Code linting
```

### Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_VOICE=true
```

## Design Principles

- **Frictionless**: Capture ideas in under 2 seconds
- **Accessible**: Works for all users and abilities
- **Responsive**: Adapts to any screen size
- **Intuitive**: Natural interactions and clear feedback

## Status

🚧 **Phase 1**: Basic capture interface and idea viewing
📋 **Next**: Real-time updates and visual integration

---

*Built for minds that move faster than fingers can type.*