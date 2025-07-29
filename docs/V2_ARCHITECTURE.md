# SP CREW CONTROL V2 - ARCHITECTURE DOCUMENTATION

## 🎯 **Paradigm Shift: From Hub-Controls-Remotes to Remote-Controls-Hub**

### **V1 Architecture (Legacy)**
```
Hub (Parent/Controller) → Forces Mode → Remotes (Children/Obey)
```

### **V2 Architecture (New)**
```
Remote (Controller) ←→ Message Relay (Coordinator) ←→ Hub (Worker)
```

---

## 🏗️ **Three-Service Architecture**

### **1. Remote Controller (Client Application)**
**Role**: User interface and control center
**Responsibilities**:
- Display hub discovery and selection interface
- Manage dual-mode UI (Single Button vs All Buttons)
- Initiate mode changes (coordinated via Message Relay)
- Send script execution requests
- Provide real-time feedback to users

**Technology**: Python + Flask + WebSocket
**Port**: 5001 (different from legacy 5000)

### **2. Message Relay (Vercel Function)**
**Role**: Session coordinator and communication hub
**Responsibilities**:
- Hub discovery registry (cross-network)
- Session management and coordination
- "Apply to all" mode synchronization
- Message routing between remotes and hubs
- Activity logging and broadcasting

**Technology**: Node.js + Vercel Functions + WebSocket proxy
**Deployment**: Vercel free tier

### **3. Hub Worker (Script Executor)**
**Role**: Pure script execution service
**Responsibilities**:
- Register with Message Relay on startup
- Execute scripts when requested
- Report execution results and status
- Activity monitoring (read-only)
- NO control over remotes

**Technology**: Python + Flask + UV script execution
**Port**: 5002 (avoid conflicts with legacy)

---

## 📡 **Communication Flow**

### **Startup Sequence**
1. **Hub Worker** starts → registers with **Message Relay**
2. **Remote Controller** starts → requests hub list from **Message Relay**
3. User selects hub → **Remote** joins session via **Message Relay**
4. **Message Relay** coordinates session setup → **Remote** connects to **Hub**

### **Mode Change Flow** 
1. **Remote A** requests "All Buttons" mode → **Message Relay**
2. **Message Relay** broadcasts mode change → **All Remotes in session**
3. **All Remotes** prepare UI transition → notify **Message Relay** ready
4. **Message Relay** coordinates simultaneous transition → **All Remotes** complete

### **Script Execution Flow**
1. **Remote** sends script request → **Hub Worker** (via **Message Relay**)
2. **Hub Worker** executes script → returns result → **Remote**
3. **Hub Worker** logs activity → **Message Relay** → broadcasts to session

---

## 🗂️ **Directory Structure**

```
crew-control/
├── legacy/                          # V1 system (preserved as backup)
│   ├── hub.py                      # Original 1783-line hub
│   └── remote/                     # Original remote system
├── v2/                             # V2 clean architecture
│   ├── hub-worker/                 # Hub Worker Service
│   │   ├── app.py                  # Main application
│   │   ├── script_executor.py      # UV script execution
│   │   ├── activity_logger.py      # Activity tracking
│   │   ├── relay_client.py         # Message Relay communication
│   │   └── templates/              # Monitoring interface
│   ├── remote-controller/          # Remote Controller Service
│   │   ├── app.py                  # Main application
│   │   ├── hub_discovery.py        # Hub finding and selection
│   │   ├── mode_manager.py         # UI mode coordination
│   │   ├── button_grid.py          # All Buttons mode UI
│   │   └── templates/              # Remote interface
│   └── message-relay/              # Vercel Function
│       ├── api/                    # Vercel API routes
│       │   ├── discover-hubs.js    # Hub discovery endpoint
│       │   ├── join-session.js     # Session management
│       │   └── broadcast.js        # Message broadcasting
│       ├── lib/                    # Shared utilities
│       │   ├── session-manager.js  # Session state management
│       │   └── websocket-proxy.js  # WebSocket message routing
│       └── vercel.json             # Vercel configuration
├── shared/                         # Common resources
│   ├── themes/                     # Unified cyberpunk styling
│   │   ├── cyberpunk.css          # Main theme
│   │   └── components.css         # Reusable components
│   └── protocols/                  # Communication protocols
│       └── message_protocol.json  # Complete message specification
└── docs/                           # Documentation
    ├── SYSTEM_SPECIFICATION.md    # User requirements
    ├── V2_ARCHITECTURE.md         # This file
    └── DEPLOYMENT_GUIDE.md        # Setup instructions
```

---

## 🔄 **Message Flow Patterns**

### **Hub Discovery Pattern**
```
Remote → Relay: hub_discovery_request
Relay → Remote: hub_discovery_response (with hub list)
```

### **Session Joining Pattern**
```
Remote → Relay: session_join_request
Relay → Hub: validate_remote_join
Hub → Relay: join_approval
Relay → Remote: session_join_response (with websocket_url)
```

### **Mode Coordination Pattern**
```
Remote A → Relay: mode_change_request
Relay → All Remotes: mode_change_broadcast
All Remotes → Relay: mode_transition_ready
Relay → All Remotes: mode_transition_complete
```

### **Script Execution Pattern**
```
Remote → Hub: script_execution_request (via Relay)
Hub → Remote: script_execution_response (via Relay)  
Hub → Relay: activity_log (for broadcasting)
Relay → All Session: activity_log_broadcast
```

---

## 🛡️ **Security & Reliability**

### **Security Measures**
- **Session-based authentication**: No permanent credentials stored
- **Message validation**: All messages validated against protocol schema
- **Rate limiting**: Prevent script execution spam
- **Input sanitization**: All user inputs sanitized

### **Reliability Features**
- **Connection monitoring**: Detect and handle network failures
- **Graceful degradation**: Fallback behaviors for service failures  
- **Retry logic**: Exponential backoff for reconnections
- **State synchronization**: Keep all session participants in sync

### **Error Handling**
- **Hub unavailable**: Return to discovery, show clear error
- **Mode transition failure**: Rollback to previous mode
- **Network interruption**: Automatic reconnection with user feedback
- **Service overload**: Queue management and user notification

---

## 📊 **Performance Optimizations**

### **Latency Reduction**
- **Direct WebSocket connections** between Remote and Hub (after initial coordination)
- **Message batching** for multiple rapid button presses
- **Local caching** of hub lists and session state
- **Predictive prefetching** of likely-needed resources

### **Scalability Features**
- **Stateless Message Relay** (can scale horizontally)
- **Hub Worker isolation** (each hub independent) 
- **Session partitioning** (sessions don't interfere)
- **Resource pooling** (efficient WebSocket connection reuse)

---

## 🔄 **Migration Strategy**

### **Phase 1: Parallel Deployment**
- V2 system runs alongside V1 (different ports)
- Users can choose which version to use
- Both systems share same script directory

### **Phase 2: Gradual Migration** 
- Test V2 with subset of users
- Migrate configurations and preferences
- Monitor performance and stability

### **Phase 3: Full Cutover**
- Default to V2 system for new users
- Provide V1 fallback option during transition
- Eventually retire V1 after proven stability

### **Rollback Plan**
- V1 system preserved and immediately available
- Configuration migration is reversible
- Clear documentation for reverting to V1

---

## ✅ **Success Metrics**

### **Maintainability Goals**
- ✅ Each file has single, clear responsibility  
- ✅ Easy to locate and modify specific functionality
- ✅ Clear separation between business logic and UI
- ✅ Comprehensive documentation for future development

### **Performance Goals** 
- ✅ Sub-second response times for all user interactions
- ✅ Real-time updates without page refreshes
- ✅ Cross-network functionality (Arkansas ↔ New Jersey)
- ✅ Support for rapid button presses (game-like experience)

### **User Experience Goals**
- ✅ Intuitive hub discovery and selection
- ✅ Smooth mode transitions without disruption
- ✅ Clear feedback for all user actions
- ✅ Unified cyberpunk aesthetic across all interfaces