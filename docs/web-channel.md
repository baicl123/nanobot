# Web Channel Implementation Guide

## Overview
The Web Channel enables nanobot to be accessed via a web interface, providing enterprise internal users with a modern, intuitive chat experience. It supports multi-user isolation, session management, and real-time communication.

## Architecture
```
┌─────────────────┐    WebSocket    ┌─────────────────┐    MessageBus    ┌─────────────────┐
│   Browser       │ ◄──────────────► │  FastAPI Server │ ◄──────────────► │   nanobot Core  │
│  (React + Vite) │   HTTP API      │  (Web Channel)  │                  │                 │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
          │                                     │
          ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│  Static Assets  │                  │   SQLite DB     │
│  (HTML/CSS/JS)  │                  │ (Session Meta)  │
└─────────────────┘                  └─────────────────┘
```

## Core Features

### 1. User Isolation
- Each user is identified by `empId` passed via URL parameter
- All sessions and data are isolated per user
- Permissions are controlled via the existing `allow_from` configuration

### 2. Session Management
- Users can create multiple independent chat sessions
- Session metadata (name, last message, timestamps) stored in SQLite for fast querying
- Actual message history stored in JSONL files (compatible with existing nanobot storage)

### 3. Real-time Communication
- WebSocket-based for low-latency messaging
- Support for streaming responses (typing effect)
- Support for progress updates and tool call hints

### 4. Integration with Existing System
- Reuses nanobot's core session system, no changes to existing logic
- Reuses existing permission system (`allow_from`)
- Reuses existing message processing pipeline
- No impact on other channels (CLI, Telegram, Feishu, etc.)

## Configuration
Add the following to your `config.json`:
```json
{
  "channels": {
    "web": {
      "enabled": true,
      "host": "0.0.0.0",
      "port": 18791,
      "allow_from": ["60079031", "60079032"],
      "cors_origins": ["https://nanobot.company.com"]
    }
  }
}
```

### Configuration Options
| Field | Type | Description |
|-------|------|-------------|
| `enabled` | `boolean` | Enable/disable the web channel |
| `host` | `string` | Host address to bind to |
| `port` | `number` | Port to listen on (default: 18791) |
| `allow_from` | `string[]` | List of allowed employee IDs. Use `["*"]` to allow all internal users. |
| `cors_origins` | `string[]` | List of allowed CORS origins for frontend deployment |

## Storage Structure
```
workspace/
├── memory/                    # Global memory (shared across all channels)
├── sessions/                  # Global sessions (shared across all channels except web)
├── skills/                    # Global skills (shared across all users)
├── web.db                     # Web channel SQLite database (session metadata)
└── users/                     # Web channel user isolation layer
    ├── {empId}/               # Individual user workspace
    │   ├── memory/            # User-specific cross-session memory
    │   ├── sessions/          # User-specific session messages (JSONL files)
    │   └── skills/            # User-specific personal skills (reserved)
```

## API Endpoints
For detailed API documentation, see [web-api.md](./web-api.md).

## Deployment

### Single Container Deployment (Recommended)
1. Build the React frontend and copy assets to `nanobot/web/static/`
2. Configure the web channel in `config.json`
3. Run nanobot as usual - the web server will start automatically when the channel is enabled

### Reverse Proxy Deployment
1. Configure Nginx/Traefik to forward requests to the web channel port
2. Ensure WebSocket upgrade is enabled in the proxy configuration:
   ```nginx
   location /ws {
       proxy_pass http://localhost:18791/ws;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
       proxy_set_header Host $host;
   }
   ```

## Security
- No built-in authentication - intended for internal enterprise use behind SSO
- User identity is passed via URL parameters from the enterprise portal/SSO
- Permissions are enforced via `allow_from` list
- CORS configuration restricts which domains can access the API

## Frontend Development
The frontend is built with React 18 + Vite + Ant Design. The source code is maintained in a separate repository. To deploy:
1. Build the frontend with `npm run build`
2. Copy all files from the `dist/` directory to `nanobot/web/static/`
3. Restart nanobot to serve the updated static assets

## Compatibility
- Python 3.10+
- Works with all existing nanobot features (tools, skills, memory, etc.)
- Can run alongside other channels simultaneously
