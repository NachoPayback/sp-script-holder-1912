# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 **CURRENT GOAL: SP CREW CONTROL V2 REWRITE**

**CRITICAL UNDERSTANDING:**
- **V2 Architecture:** WebSocket-based real-time messaging through Vercel relay
- **Core Flow:** Remote WebSocket → Vercel Relay → Hub WebSocket (millisecond response)
- **Cross-Network:** One remote can control MULTIPLE hubs internationally
- **Session Coordination:** Mode changes apply to ALL remotes in session instantly
- **Real-Time:** Button presses must execute scripts instantly, no REST API delays

## 🧠 **CORE METHODOLOGY & MINDSET**

**Real-Time WebSocket Matrix Architecture:**
```
Multiple Remotes ←→ Vercel Relay Coordinator ←→ Multiple Hubs
```

**Fundamental Principles:**
1. **Many-to-Many Connection:** Any number of remotes can control any number of hubs simultaneously
2. **Session-Based Coordination:** Groups of remotes share session state (mode, assignments)
3. **Instant Message Routing:** Button press → WebSocket message → target hub in milliseconds
4. **Broadcast Synchronization:** Changes to session affect ALL participants immediately
5. **Location Agnostic:** Hubs can be anywhere globally, examples are theoretical only

**Connection Matrix:**
- **Remote-to-Hub:** One remote can control multiple hubs in same session
- **Hub-to-Remote:** One hub can be controlled by multiple remotes simultaneously  
- **Session Coordination:** Mode changes (Single ↔ All Buttons) apply to ALL remotes in session
- **Real-Time Broadcasting:** Any change broadcasts to ALL session participants instantly

**Message Flow:**
1. **Button Press:** Remote → Relay (routes to target hub) → Hub executes → Result back
2. **Mode Change:** Remote → Relay → Broadcast to ALL remotes in session
3. **Session Updates:** Any change synchronizes ALL participants in real-time

**Success Criteria:**
- **<100ms execution time** globally
- **Instant synchronization** when any remote changes session state
- **Scalable architecture** supporting any number of remotes/hubs
- **Location independence** - works anywhere internationally

**🚨 CRITICAL:** This is a real-time messaging coordinator, NOT REST APIs. WebSocket persistent connections only.

## 🔧 **V2 SYSTEM ARCHITECTURE**

### **Message Relay (Vercel - DEPLOYED)**
- **Location:** `v2/message-relay/` 
- **URL:** https://sp-script-holder-1912.vercel.app
- **Purpose:** WebSocket coordinator for international hub/remote communication
- **Technology:** Vercel serverless functions with WebSocket support
- **Status:** Needs WebSocket rebuild for real-time coordination

### **Hub Worker (Python)**
- **Location:** `v2/hub-worker/app.py`
- **Purpose:** Pure script executor that connects to relay via WebSocket
- **Technology:** Python Flask + WebSocket client
- **Status:** Needs WebSocket client integration

### **Remote Controller (Python)**
- **Location:** `v2/remote-controller/app.py`
- **Purpose:** Web UI for button presses, connects to relay via WebSocket
- **Technology:** Python Flask + WebSocket client + web interface
- **Status:** Needs WebSocket client integration

## 🎮 **CORE FEATURES THAT MUST WORK**

### **Real-Time Button Execution**
- Remote presses button → WebSocket message → Relay routes → Hub executes → Result back
- **NO HTTP REQUEST/RESPONSE DELAYS**
- Response time: milliseconds internationally

### **Session Coordination (ALL REMOTES AT ONCE)**
- **Mode Switching:** Single Button ↔ All Buttons affects ALL remotes in session
- **Shuffle:** Reassigns scripts to ALL remotes simultaneously  
- **Real-Time Updates:** When one remote changes mode, others see it instantly

### **Multi-Hub Control**
- One remote can control multiple hubs globally
- "All Buttons" mode shows scripts from ALL hubs in session
- Message routing: `{"target_hub": "hub_id", "script": "script_name"}`

### **Session Management**
- Multiple remotes join same session
- Session includes multiple hubs
- Coordinator tracks: who's in session, current mode, script assignments
- Real-time sync between all participants

## 📨 **MESSAGE PROTOCOL**

### **WebSocket Message Format**
```json
{
  "type": "execute_script|change_mode|shuffle|join_session",
  "session_id": "session_123",
  "target_hub": "hub_id",
  "script_name": "move_mouse",
  "remote_id": "remote_123",
  "data": {}
}
```

### **Communication Flows**
1. **Execute Script:** Remote → Relay → Hub → Relay → Remote (result)
2. **Mode Change:** Remote → Relay → ALL remotes in session (instant update)
3. **Shuffle:** Remote → Relay → ALL remotes get new assignments
4. **Session Updates:** Any change broadcasts to ALL session participants

## 🚨 **CRITICAL SUCCESS CRITERIA**

1. **Button press to script execution: < 100ms response time**
2. **Mode changes apply to ALL remotes instantly**
3. **One remote can control multiple international hubs**
4. **Real-time coordination without page refreshes**
5. **WebSocket persistent connections, not REST APIs**

## 📁 **PROJECT STRUCTURE**

```
v2/
├── message-relay/          # Vercel WebSocket coordinator (DEPLOYED)
│   ├── api/               # Serverless functions
│   └── package.json       # Node.js dependencies
├── hub-worker/            # Python script executor
│   ├── app.py            # WebSocket client + Flask monitoring
│   └── requirements.txt   # Python dependencies
└── remote-controller/     # Python web interface
    ├── app.py            # WebSocket client + Flask web UI
    └── requirements.txt   # Python dependencies
```

## 🎯 **IMMEDIATE OBJECTIVES**

1. **Rebuild Message Relay:** WebSocket-based coordination in Vercel
2. **Update Hub Worker:** WebSocket client connection to relay
3. **Update Remote Controller:** WebSocket client for real-time button presses
4. **Test Integration:** Verify cross-network real-time script execution
5. **Deploy & Validate:** Ensure millisecond response times internationally

## 💻 **DEVELOPMENT COMMANDS**

### **Test V2 Components**
```bash
# Test Hub Worker
cd v2/hub-worker
python app.py --port 5002

# Test Remote Controller  
cd v2/remote-controller
python app.py --port 5001

# Deploy Message Relay
cd v2/message-relay
# (Vercel auto-deploys from GitHub)
```

### **Legacy System (V1 - PRESERVED)**
```bash
# Old system in legacy/ folder - DO NOT MODIFY
cd legacy/src
python hub.py      # Old hub (port 5000)
cd legacy/src/remote  
python remote_app.py  # Old remote (port 5001)
```

## 🔄 **MESSAGE FLOW EXAMPLE**

**Button Press Flow:**
1. User presses "Move Mouse" on Remote Controller web UI
2. Remote sends WebSocket: `{"type":"execute_script","script":"move_mouse","target_hub":"hub_location_1"}`
3. Vercel Relay routes message to target Hub WebSocket
4. Target Hub executes move_mouse.py script
5. Hub sends result back through Relay to Remote
6. Remote UI updates with execution status
7. **Total time: <100ms internationally**

**Mode Change Flow:**
1. Remote A clicks "All Buttons" mode
2. Remote A sends: `{"type":"change_mode","mode":"all_buttons","session":"abc123"}`
3. Relay updates session mode
4. Relay broadcasts to ALL remotes in session: mode changed
5. Remote B, C, D instantly switch to All Buttons view
6. **All remotes synchronized in real-time**

---

**🚨 REMEMBER: This is real-time messaging system, NOT REST APIs. WebSocket persistent connections for instant response.**