# CREW CONTROL REFACTOR REQUIREMENTS

## 📝 **Instructions**
Fill in your answers after each `ANSWER:` field. Use specific values like `YES/NO`, `KEEP/REMOVE/MODIFY`, or detailed descriptions. Focus on FUNCTIONALITY, not implementation details.

---

## 🔍 **EXISTING FEATURES AUDIT**

### **Core Hub Functionality**

1. **Silent Background Operation** 
   - **What it does**: Hub runs as a background process without showing any console windows. Uses Windows mutex to prevent multiple instances. Critical for stealth operation.
   - **Current behavior**: Hub.exe launches silently, creates logs in logs/ directory, writes hub_info.txt for debugging
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep

2. **Script Execution System**
   - **What it does**: Hub manages a pool of 13+ prank scripts (Python, PowerShell, batch files). Each script has auto-detected dependencies. Scripts execute via UV Python environment with timeout protection.
   - **Current behavior**: Scripts stored in scripts/ directory, dependencies auto-scanned and installed, executed with 30-second timeout
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep

3. **Remote Management System**
   - **What it does**: Hub tracks connected remotes, assigns each remote exactly one script, manages pairing tokens, handles remote discovery. Shows remote status, usernames, last-seen times.
   - **Current behavior**: Each remote gets unique script assignment, automatic cleanup of offline remotes after 2 minutes, manual removal via ✕ buttons
   - **Keep/Remove/Modify**: 
   - ANSWER: Modify, this will eventually have an "all buttons mode", but yes the DEFAULT behavior would be "each remote gets exactly one script, so for the most part this is correct"

4. **Script Shuffling System**
   - **What it does**: Reassigns scripts to different remotes either manually (hub button) or automatically (timer). Ensures no two remotes have the same script.
   - **Current behavior**: Manual shuffle via web UI, optional timer-based auto-shuffle every X minutes, broadcasts new assignments to all remotes
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep

5. **Hub Activation Toggle**
   - **What it does**: Hub can be "deactivated" without shutting down - remotes can still connect but button presses are ignored. Allows preparation/maintenance without stopping the system.
   - **Current behavior**: Toggle button in web UI, when inactive all script execution requests return "Hub inactive" error
   - **Keep/Remove/Modify**: 
   - ANSWER: Remove

6. **Git-Based Script Updates**
   - **What it does**: Hub can pull latest scripts from configured Git repository, automatically scan for new dependencies, and update available script pool without restart.
   - **Current behavior**: "Update Scripts" button triggers git pull, dependency scanning, script pool reload, assignment updates
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep OR modify, brainstorm a better system

7. **System Information Hotkey**
   - **What it does**: Press Ctrl+Alt+S+P anywhere on the system to display hub status in console (name, ID, active remotes, status).
   - **Current behavior**: Global hotkey using pynput, shows popup info even when hub is running silently
   - **Keep/Remove/Modify**: 
   - ANSWER: Remove, this hotkey's been useless for us and we changed to allow for a web ui for the hub

### **Hub Control Interface**

8. **Hub Web Dashboard**
   - **What it does**: Web interface at http://127.0.0.1:5000 for monitoring and controlling the hub. Shows real-time remote status, provides control buttons, displays statistics.
   - **Current behavior**: Dark cyberpunk theme, auto-refreshing status, buttons for shuffle/toggle/cleanup/shutdown, remote cards with online/offline status
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep but we will modify and unify the theme with the remotes.

### **Remote Functionality**

9. **Single-Button Remote Interface**
   - **What it does**: Each remote shows one large button with the name of its assigned script. Press button to execute that script on the hub.
   - **Current behavior**: Big central button, displays script name, shows success/failure feedback, cyberpunk styling
   - **Keep/Remove/Modify**: 
   - ANSWER: Keep BUT modify, as we will add an "all buttons" mode. Keep in mind that script name is OPTIONAL as per the "show function name" feature. Success/failure doesn't ever really show just by the way

10. **Remote Auto-Discovery & Pairing**
    - **What it does**: Remotes automatically find available hubs on the network, pair with them using tokens, and maintain persistent connections.
    - **Current behavior**: Scans for hubs on startup, displays available hubs, stores pairing info in config files, reconnects automatically
    - **Keep/Remove/Modify**: 
    - ANSWER: This is very useful, but you always say "on the network" implying it cannot find REMOTE hubs, implying that if on different networks, this connection will fail. Is there a better long distance communication method/what tools can we use to make connection secure, any distance, FAST, and most importantly, at no cost.

11. **Remote Identity System**
    - **What it does**: Each remote has a unique ID and optional username. Hub displays these for identification and management.
    - **Current behavior**: Auto-generated Remote-XXXXXXXX IDs, user-settable usernames, displayed in hub interface and logs
    - **Keep/Remove/Modify**: 
    - ANSWER: Identity system is a yes, however you need to modify your internal understanding as i believe you often jumble these ideas or allow for overlapping/redundant identities

12. **Real-Time Synchronization**
    - **What it does**: Remotes receive instant updates when scripts are shuffled, hub status changes, or assignments change. No page refresh needed.
    - **Current behavior**: NATS pub/sub messaging, JavaScript updates UI immediately, maintains connection status
    - **Keep/Remove/Modify**: 
    - ANSWER: No page refresh is a huge must, this is basically a remote GAME akin to Jackbox games.

---

## 🆕 **NEW FEATURE: "ALL BUTTONS" MODE**

### **Overview**
Currently, each remote shows ONE big button with their assigned script. The new "All Buttons" mode would show ALL available scripts as a grid of buttons on every remote, turning each remote into a complete control panel.

### **Core Functionality Questions**

13. **Mode Toggle Behavior**
    - **What it affects**: When you toggle "All Buttons" mode on the hub, should it instantly change ALL connected remotes to show the full button grid?
    - **Current flow**: Hub controls everything, remotes just display what they're told
    - **Question**: Should remotes switch modes instantly, or do they need to be notified and update when ready?
    - ANSWER: It should DISALLOW any other input, basically going "hang on while we update" and then REALLOW input after the ui has fully updated. Whatever COMMUNICATION system is SAFER and SMARTER, I'm all ears, as it seems we may have overcomplicated our communication.

14. **Button Grid Design**
    - **What it replaces**: Instead of one big button, show a grid of ~13 smaller buttons (one for each script)
    - **Script identification**: Each button shows the script name (like "Move Mouse", "Play Sound", etc.)
    - **Visual question**: How should these buttons be arranged? 3x5 grid? 4x4 grid? Auto-adjust to screen size?
    - ANSWER: This needs to be reactive, given that new scripts may be added. Reactive grids are your friend.

15. **Button Press Behavior**
    - **Current**: Press one button → script executes → wait for feedback
    - **New question**: In grid mode, can users rapidly press multiple different buttons? Should there be a cooldown? Should all remotes see who pressed what?
    - **Example scenario**: Remote A presses "Move Mouse", Remote B presses "Play Sound" 2 seconds later
    - ANSWER: In an ideal world, all scripts are spammable with minimal "punishment"

16. **Script Assignment Logic**
    - **Current system**: Each remote is assigned exactly one script, no duplicates allowed
    - **New question**: In "All Buttons" mode, what happens to script assignments? 
      - Option A: Assignments become irrelevant (everyone sees everything)
      - Option B: Your "assigned" script is highlighted/special in the grid
      - Option C: Something else?
    - ANSWER: Assignments become irrelevant. All users get all scripts. It's "god mode"

17. **Shuffle System Integration**
    - **Current**: Shuffle reassigns which remote gets which single script
    - **New question**: What does "shuffle" mean when everyone can press any button?
      - Option A: Disable shuffle entirely in "All Buttons" mode
      - Option B: Shuffle changes button positions/highlighting
      - Option C: Shuffle still assigns "primary" scripts but doesn't restrict access
    - ANSWER: Shuffle is disabled in all buttons mode

### **Hub Control Questions**

18. **Mode Control Interface**
    - **What you need**: A way to switch between "Single Button" mode (current) and "All Buttons" mode (new)
    - **Question**: How prominent should this control be in the hub interface?
      - Option A: Big toggle switch prominently displayed
      - Option B: Setting buried in an admin section
      - Option C: Dropdown selector
    - ANSWER: As I've tried to demonstrate, the hub should really NOT have control of the remotes at all in my opinion. It makes me feel like we almost need an intermediary between the two, because the REMOTES send the commands, the hub should really only be responsible for RUNNING scripts, but right now it's almost like the "parent" to the remotes, which feels unsafe

19. **Activity Monitoring** 
    - **Current**: Hub logs when remotes press their assigned button
    - **New complexity**: In "All Buttons" mode, many remotes might press many different buttons
    - **Question**: Should the hub show detailed activity (who pressed what when), simple counters (X button presses), or no additional monitoring?
    - ANSWER: Who pressed what and when. Basically just "(Time) - (Person) pressed (button)"

### **User Experience Questions**

20. **Mode Switching Experience**
    - **User journey**: Hub admin toggles mode → all remotes need to change their interface
    - **Question**: Should the switch be instant (JavaScript updates the page) or require remotes to refresh their pages?
    - **Consideration**: Instant is smoother, refresh is more reliable
    - ANSWER: The hub user should never really have CONTROL of the remotes. The hub is meant to be the "worker" not the parent, that's the problem. I PREFER instant updates however that do not require page loads, if there is a system BETTER than JS for these sort of dynamic updates, I'm all ears

21. **Small Screen Handling**
    - **Problem**: 13 buttons might not fit well on phone screens or small windows
    - **Question**: How should "All Buttons" mode adapt to small screens?
      - Option A: Make buttons smaller to fit
      - Option B: Make it scrollable
      - Option C: Switch to a list view automatically
    - ANSWER: Analyze and weigh pros and cons, then get back to me

### **Configuration & Persistence**

22. **Mode Persistence**
    - **Question**: Should the "All Buttons" mode setting persist when the hub restarts?
    - **Option A**: Yes, save to config file so mode survives restarts
    - **Option B**: No, always start in "Single Button" mode for safety
    - ANSWER: No. Start in Single Button. Again, the hub should really NOT be in charge.

---

## 🏗️ **ARCHITECTURE & IMPLEMENTATION PREFERENCES**

23. **Code Organization Philosophy**
    - **Current problem**: 2,800+ lines in 2 files, hard to maintain
    - **Question**: What's your preference for the new structure?
      - Option A: Many small files (easier to find specific functionality)
      - Option B: Moderate number of well-organized files (balance of organization and simplicity)
      - Option C: Keep it simple, avoid over-engineering
    - ANSWER: Do critical analysis, do not simply make a judgement call, You are Claude Sonnet 4, how does your brain work, what structure HELPS you?

24. **Documentation Level**
    - **Question**: How much documentation do you want for the new architecture?
      - Option A: Extensive documentation explaining every component
      - Option B: Key architectural decisions and API documentation
      - Option C: Minimal documentation, code should be self-explanatory
    - ANSWER: Documentation can be handled after everything is done and set in stone, we often get distracted by documentation but the only time it should be made BEFORE the end of the project is to help you maintain context

---

## 💭 **FUTURE CONSIDERATIONS**

25. **Other Feature Ideas**
    - **Question**: Are there any other features you're considering that might affect how we architect this?
    - **Examples**: Different script categories, user permissions, remote grouping, etc.
    - ANSWER: New scripts, fuck categories, simply new scripts and the ability to have a remote change which hub it's connecting to (Like if there's a hub on computer 1 in Arkansas and then a hub on computer 2 in New Jersey, we should be able to find and choose them)

26. **Performance Concerns**
    - **Question**: Do you have any concerns about performance with the button grid, especially with many remotes connected?
    - **Context**: More buttons = more UI complexity, but shouldn't affect core functionality
    - ANSWER: At max there will be 6 remotes, so no. And as long as we make the UI replicable/templated, adding new buttons should be easy. Latency is my biggest concern

27. **Branding**
    - **Current**: "Crew Control" branding throughout the interface
    - **Question**: Keep this name or want to change it during the refactor?
    - ANSWER: I think Crew Control is a good name. You can make it SP Crew Control if you so choose

28. **Development Priorities**
    - **Question**: What's most important to get right in the new architecture?
      - Option A: Rock-solid stability (prioritize reliability)
      - Option B: Clean, maintainable code (prioritize future development)
      - Option C: Feature completeness (prioritize having all features work perfectly)
      - Option D: Performance and speed (prioritize fast response times)
    - ANSWER: B and D are the biggest factors, I ened code to be navigable and MAINTAINABLE, often with Claude projects we find ourselves lost and damage code when not even focused on that feature.

---

## ✅ **COMPLETION CHECKLIST**

- [ ] All existing features reviewed (Questions 1-12)
- [ ] All new "All Buttons" mode decisions made (Questions 13-22)  
- [ ] Architecture preferences specified (Questions 23-24)
- [ ] Future considerations documented (Questions 25-28)

**When finished**: Save this file and let me know. I'll create a comprehensive architecture plan based on your exact specifications.