# 3commas Clone - DCA Bot Trading Platform

## Current Goal
🎯 **CRITICAL: Scale & Architecture Planning** - Design for 1000+ users with 5000+ concurrent bots

---

## Phase 1: Core Layout, Authentication & Dashboard ✅
**Goal**: Establish the foundational UI structure with Material Design 3, user authentication system, and main dashboard layout.

- [x] Create base layout with Material Design 3 theme (teal primary, Roboto font, proper elevation system)
- [x] Build navigation structure (app bar, navigation drawer, bottom navigation)
- [x] Implement user authentication system (register, login, logout, session management)
- [x] Create main dashboard page with overview cards (total bots, active bots, total profit/loss, account balance)
- [x] Add user profile state management with subscription tier tracking (FREE vs PRO)
- [x] Build responsive sidebar navigation with routes for Dashboard, Bots, Exchange Settings, Subscription

---

## Phase 2: Binance Integration & Exchange Connection ✅
**Goal**: Integrate Binance API for spot trading, manage API keys securely, and display real-time account data.

- [x] Add Binance API key configuration page (API Key, Secret Key input with secure storage)
- [x] Implement Binance spot account connection and balance retrieval
- [x] Create exchange status indicator showing connection health
- [x] Build available trading pairs selector (fetch from Binance spot markets)
- [x] Display user's Binance spot wallet balances in dashboard
- [x] Add API key validation and error handling with user-friendly messages
- [x] **Store API keys per user in database** (encrypted with Fernet)
- [x] **Add immediate credential validation** before saving keys

---

## Phase 3: DCA/Martingale Bot Creation & Management ✅
**Goal**: Build complete bot creation wizard, bot list view, and bot management interface with all DCA strategy parameters.

- [x] Create "New Bot" wizard with step-by-step configuration (Material Design stepper component)
- [x] Implement DCA bot configuration form with fields: trading pair, base order size, safety order size, safety order volume scale, safety order step scale, max safety orders count, price deviation to open safety orders, take profit percentage
- [x] Build bot list page showing all user bots with status (active/paused/stopped), pair, profit/loss, deals count
- [x] Add bot detail view with configuration display, performance metrics, and deal history
- [x] Implement bot control actions (start, pause, stop, edit, delete)
- [x] Add bot limit enforcement (1 bot for FREE, 5 bots for PRO members)
- [x] Create bot status indicators with Material Design chips and colors

---

## Phase 4: Real-Time Bot Execution Engine & Deal Management ✅

### 4.1: WebSocket Price Streaming & Bot Lifecycle Management ✅
- [x] Implement Binance WebSocket connection manager using `python-binance` streams (`BinanceSocketManager`)
- [x] Create background task system for per-bot price monitoring (subscribe to ticker/kline streams per trading pair)
- [x] Build bot lifecycle state machine: STARTING → MONITORING → PLACING_ORDER → IN_POSITION → CLOSING → STOPPED
- [x] Add bot startup validation (check balance, verify trading pair, validate configuration)
- [x] Implement graceful bot shutdown with WebSocket cleanup and position safety checks
- [x] Create bot heartbeat system to detect and handle disconnections/crashes

### 4.2: DCA Strategy Logic & Safety Order Execution ✅
- [x] Build Deal model and DealState management (deal tracking per bot)
- [x] Implement Order model with full order details (order_id, timestamp, side, price, quantity, type, status)
- [x] Create deal creation logic with base order placement
- [x] Build weighted average entry price calculator
- [x] Implement add_safety_order() method to track multiple safety orders
- [x] Create update_unrealized_pnl() for real-time P/L calculation
- [x] Build close_deal() handler to finalize deals with realized P/L
- [x] Add martingale scaling calculations (volume scale and step scale)
- [x] Test complete deal lifecycle (create → add safety orders → calculate P/L → close)
- [x] Integrate deal management with bot execution state (place actual orders via Binance API)
- [x] Implement real-time price deviation monitoring and automatic safety order triggering
- [x] Add balance validation before each order placement
- [x] Build order execution wrapper with retry logic and error handling
- [x] Implement take profit logic (monitor unrealized P/L and trigger sell when target hit)
- [x] Add UI updates to show deal info, P/L, and safety order progress in bot cards

### 4.3: Take Profit, Stop Loss & Deal Closure ✅
- [x] Implement real-time profit/loss calculator based on current price vs weighted average entry
- [x] Build take profit trigger: when unrealized profit hits target % → execute sell order for entire position
- [x] Create deal closure handler: calculate final P/L, update bot statistics, save deal history
- [x] Implement auto-restart logic: if bot configured for auto-restart → immediately start new deal after closure
- [x] Add manual deal closure option with confirmation and current P/L display
- [x] Add optional stop loss logic: when loss exceeds threshold → close position at market price (skipped - not in initial scope)

### 4.4: Deal Tracking, Order History & Real-Time Updates ✅
- [x] Create Deal model: deal ID, bot ID, status (active/closed), entry time, close time, orders list, realized P/L
- [x] Build order tracking: timestamp, side (buy/sell), price, quantity, order ID, status (filled/partial/cancelled)
- [x] Implement real-time deal state broadcasting to frontend (WebSocket or SSE for live P/L updates)
- [x] Add per-bot deal history view showing all past deals with entry/exit prices and profit
- [x] Create order history table per deal showing each base/safety/take-profit order
- [x] Build portfolio-level P/L aggregation across all bots and deals
- [x] Add deal analytics: average deal duration, win rate, largest profit/loss

---

## Phase 5: Polar Subscription Integration & Payment Flow ✅
**Goal**: Integrate Polar for PRO subscription management at $10/month, handle upgrades, and enforce tier limits.

- [x] Set up Polar API integration and webhook handling
- [x] Create subscription/upgrade page with PRO tier benefits display (5 bots, future features)
- [x] Implement Polar checkout flow for $10/month PRO subscription
- [x] Build subscription status display in user profile (current tier, renewal date, payment history)
- [x] Add webhook endpoint to handle subscription events (activation, renewal, cancellation)
- [x] Implement subscription tier enforcement across bot creation and limits
- [x] Create "Upgrade to PRO" prompts when FREE users hit bot limit

---

## Phase 6: Analytics, Notifications & Polish ✅
**Goal**: Add comprehensive performance analytics, user notifications for bot events, and final UI polish.

- [x] Build performance analytics dashboard with charts (profit/loss over time, win rate, total volume traded)
- [x] Add per-bot performance metrics visualization (deals chart, profit distribution)
- [x] Implement notification system for important bot events (deal opened, take profit hit, errors, low balance warnings)
- [x] Create activity feed showing recent bot actions and trades
- [x] Add data export functionality (CSV export for deals and orders)
- [x] Implement proper error handling and user feedback throughout the app
- [x] Final UI polish: loading states, empty states, error states, responsive design verification
- [x] Add user settings page (notification preferences, display preferences)

---

## Phase 7: Database Integration with SQLite ✅
**Goal**: Add persistent data storage using SQLite and SQLAlchemy for production readiness.

- [x] Install SQLAlchemy and create database models (User, Bot, Deal, Order, Subscription)
- [x] Create database initialization and migration scripts
- [x] Implement User model with authentication fields (email, hashed password, subscription tier)
- [x] Build Bot model with all configuration fields and relationships
- [x] Create Deal and Order models with foreign keys to Bot
- [x] Implement database session management and connection pooling
- [x] Migrate AuthState to use database instead of in-memory dictionaries
- [x] Migrate BotsState to persist bots to database
- [x] Migrate DealState to persist deals and orders to database
- [x] Add database queries for analytics (aggregate P/L, win rate, etc.)
- [x] Implement secure API key encryption in database
- [x] Add database backup and migration utilities

---

## Phase 8: Binance Testnet Support ✅
**Goal**: Add environment-based toggle between Binance live and testnet for safe testing.

- [x] Add BINANCE_TESTNET environment variable (true/false)
- [x] Update ExchangeState to detect testnet mode from environment
- [x] Configure Binance client with testnet base URLs when BINANCE_TESTNET=true
- [x] Add testnet indicator badge in UI (show "TESTNET MODE" banner when active)
- [x] Update WebSocket connections to use testnet endpoints in test mode
- [x] Add testnet-specific error handling and logging
- [x] Document testnet setup in README (how to get testnet API keys, configure env)
- [x] Test full bot execution flow on Binance testnet
- [x] Add testnet balance display with clear "TEST FUNDS" label

---

## Phase 9: Security Enhancements ✅
**Goal**: Implement production-grade security with bcrypt password hashing and email verification.

- [x] Install bcrypt and add to requirements.txt
- [x] Create password hashing functions with bcrypt (hash_password, verify_password)
- [x] Update User model with email_verified, verification_token, verification_token_expires fields
- [x] Implement password strength validation (min 8 chars, uppercase, lowercase, number)
- [x] Add verification token generation (UUID-based with 24-hour expiration)
- [x] Update registration flow to hash passwords with bcrypt
- [x] Block login attempts for unverified email addresses
- [x] Create email verification page at /verify-email/[token]
- [x] Add token expiration checks and validation
- [x] Implement simulated email sending (log verification links to console)
- [x] Add toast notifications with verification links for demo
- [x] Update CRUD functions to handle verification tokens
- [x] Test complete verification flow (register → verify → login)

---

## Phase 10: Complete Database Integration ✅
**Goal**: Fix critical gaps by connecting all state management to persistent database storage.

### 10.1: Enhanced CRUD Operations ✅
- [x] Add comprehensive bot CRUD functions (create, read, update, delete)
- [x] Implement deal persistence with full lifecycle support
- [x] Add order tracking with status updates
- [x] Create get_all_running_bots() for startup recovery
- [x] Build update_bot_stats() for P/L and deal count tracking

### 10.2: BotsState Database Migration ✅
- [x] Load bots from database on app startup using user_id
- [x] Persist new bots to database in add_bot()
- [x] Update bot status in database via set_bot_status()
- [x] Update bot statistics in database via update_bot_stats()
- [x] Delete bots from database in remove_bot()
- [x] Sync in-memory bot list with database

### 10.3: DealState Database Migration ✅
- [x] Load active deals from database on page load
- [x] Persist deals to database in create_deal()
- [x] Save orders to database when created
- [x] Update deals in database when modified
- [x] Close deals in database with realized P/L

### 10.4: Bot Cleanup on Stop ✅
- [x] Cancel pending limit orders on Binance when bot stopped
- [x] Implement _cancel_pending_orders() helper method
- [x] Update database with final deal state on stop
- [x] Graceful WebSocket cleanup with order cancellation

### 10.5: Auto-Restart on App Startup ✅
- [x] Query database for running bots on startup
- [x] Resume WebSocket connections for active bots
- [x] Restore deal monitoring and price streaming
- [x] Add on_load handler to trigger restore_active_bots()

### 10.6: Balance Retry Mechanism ✅
- [x] Create poll_balances_for_pending_orders() background task
- [x] Check bots in 'waiting_for_balance' status every 60 seconds
- [x] Retry safety order placement when balance available
- [x] Update bot status back to 'monitoring' on success

### 10.7: Error Recovery UI ✅
- [x] Add "Retry" button for bots in 'error' status
- [x] Implement reset_bot_error() event handler
- [x] Allow bot restart after error state cleared
- [x] Show error reason in UI with recovery options

### 10.8: API Key Database Storage & Validation ✅
- [x] Remove LocalStorage dependency for API keys
- [x] Store API keys per user in database (encrypted with Fernet)
- [x] Add immediate validation before saving (test with client.get_account())
- [x] Load API keys from database on app startup
- [x] Show clear error messages if validation fails

---

## 🚨 PHASE 11: SCALE & ARCHITECTURE REDESIGN

**Goal**: Redesign architecture to support 1000+ users with 5000+ concurrent bots without hitting rate limits.

### 11.1: Current Bottlenecks & Limitations Analysis
- [ ] Document current WebSocket architecture (1 WebSocket per bot per pair)
- [ ] Identify Binance API rate limits (REST API: 1200 req/min, WebSocket: 300 connections)
- [ ] Calculate resource usage: 5000 bots = 5000 WebSockets if all different pairs
- [ ] Analyze polling frequency impact (5-second order polling × 5000 bots = 1000 req/sec)
- [ ] Identify memory usage per bot/WebSocket connection
- [ ] Document single-server limitations (CPU, memory, network I/O)

### 11.2: Binance User Data Stream Implementation (CRITICAL)
- [ ] Research Binance User Data Stream WebSocket API for order updates
- [ ] Implement listen key generation and renewal (60-minute expiration)
- [ ] Subscribe to executionReport events for real-time order fills
- [ ] Replace 5-second polling with event-driven order status updates
- [ ] Add outboundAccountPosition events for balance updates
- [ ] Implement automatic listen key refresh every 30 minutes
- [ ] Test User Data Stream with multiple concurrent orders
- [ ] **Expected Impact**: Eliminate 1000 req/sec polling load, instant order notifications

### 11.3: WebSocket Connection Pooling & Multiplexing
- [ ] Implement shared WebSocket connections per trading pair (not per bot)
- [ ] Create WebSocket pool manager: 1 connection serves multiple bots on same pair
- [ ] Add subscription manager: track which bots need updates from each connection
- [ ] Implement connection health monitoring and auto-reconnect
- [ ] Add graceful degradation when WebSocket limit reached
- [ ] **Expected Impact**: 5000 bots on 100 unique pairs = 100 WebSockets (not 5000)

### 11.4: Background Task Optimization
- [ ] Replace per-bot asyncio tasks with centralized bot manager
- [ ] Implement task pooling: 1 task monitors multiple bots
- [ ] Add batch processing for order status checks
- [ ] Optimize database queries with bulk operations
- [ ] Implement connection pooling for AsyncClient instances
- [ ] Add circuit breakers for API rate limit protection
- [ ] **Expected Impact**: Reduce from 5000 concurrent tasks to ~50 manager tasks

### 11.5: Database Optimization for Scale
- [ ] Add database indexes on frequently queried columns (user_id, bot_id, status)
- [ ] Implement query result caching for read-heavy operations
- [ ] Add database connection pooling (SQLAlchemy pool_size, max_overflow)
- [ ] Migrate from SQLite to PostgreSQL for production
- [ ] Implement read replicas for analytics queries
- [ ] Add database query monitoring and slow query logging
- [ ] **Expected Impact**: Handle 1000+ concurrent database operations

### 11.6: Redis Cache Layer
- [ ] Install Redis and redis-py library
- [ ] Cache user API keys (encrypted) in Redis for fast access
- [ ] Store active bot configurations in Redis
- [ ] Implement WebSocket subscription state in Redis
- [ ] Add distributed lock mechanism for order placement
- [ ] Cache trading pair metadata and exchange info
- [ ] **Expected Impact**: Reduce database load by 80%, faster bot startup

### 11.7: Horizontal Scaling Architecture
- [ ] Design stateless bot execution workers
- [ ] Implement message queue (Redis Queue or Celery) for bot commands
- [ ] Add worker nodes that consume bot execution tasks
- [ ] Implement centralized WebSocket manager service
- [ ] Add load balancer for distributing bots across workers
- [ ] Design failover and bot migration between workers
- [ ] **Expected Impact**: Scale from 1 server to N workers, handle 10,000+ bots

### 11.8: Rate Limit Management
- [ ] Implement token bucket algorithm for API rate limiting
- [ ] Add per-user rate limit tracking
- [ ] Create priority queue for order execution (critical orders first)
- [ ] Implement request batching where possible
- [ ] Add exponential backoff for rate limit errors
- [ ] Create rate limit monitoring dashboard
- [ ] **Expected Impact**: Never hit Binance rate limits, predictable performance

### 11.9: Monitoring & Observability
- [ ] Add Prometheus metrics for bot performance
- [ ] Implement Grafana dashboards for system health
- [ ] Add alerts for WebSocket disconnections
- [ ] Track API usage per endpoint
- [ ] Monitor database query performance
- [ ] Add user-facing status page (system health, active bots)
- [ ] **Expected Impact**: Proactive issue detection, 99.9% uptime

### 11.10: Testing Scale Limits
- [ ] Create load testing script: simulate 1000 users with 5 bots each
- [ ] Test WebSocket connection limits (max concurrent connections)
- [ ] Test API rate limits under load
- [ ] Measure database performance with 10,000+ active deals
- [ ] Test failover scenarios (server restart, network issues)
- [ ] Benchmark memory usage and CPU usage per bot
- [ ] Document maximum capacity per server/worker node

---

## 📊 Scale Architecture Overview

### Current Architecture (Phase 1-10) ⚠️
```
[User Browser] → [Reflex Server] → [Per-Bot WebSocket] → [Binance API]
                       ↓
                [SQLite Database]
                       ↓
                [Per-Bot Async Task (5000 tasks for 5000 bots)]
```

**Limitations:**
- 1 WebSocket per bot = 5000 connections for 5000 bots
- 5-second polling = 1000 API requests/second
- No connection pooling
- Single server bottleneck
- SQLite not suitable for concurrent writes

---

### Target Architecture (Phase 11) ✅

```
                    ┌─────────────────────────────────┐
                    │   Load Balancer / Nginx         │
                    └─────────────────────────────────┘
                                 ↓
        ┌────────────────────────┼────────────────────────┐
        ↓                        ↓                        ↓
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Reflex Web    │      │ Reflex Web    │      │ Reflex Web    │
│ Server 1      │      │ Server 2      │      │ Server N      │
└───────────────┘      └───────────────┘      └───────────────┘
        ↓                        ↓                        ↓
        └────────────────────────┼────────────────────────┘
                                 ↓
                    ┌─────────────────────────────────┐
                    │   Redis Cache & Message Queue   │
                    │   - API Keys Cache              │
                    │   - Bot Configs Cache           │
                    │   - WebSocket State             │
                    │   - Task Queue                  │
                    └─────────────────────────────────┘
                                 ↓
        ┌────────────────────────┼────────────────────────┐
        ↓                        ↓                        ↓
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│ Bot Worker 1  │      │ Bot Worker 2  │      │ Bot Worker N  │
│ - 100 bots    │      │ - 100 bots    │      │ - 100 bots    │
│ - Shared WS   │      │ - Shared WS   │      │ - Shared WS   │
└───────────────┘      └───────────────┘      └───────────────┘
        ↓                        ↓                        ↓
        └────────────────────────┼────────────────────────┘
                                 ↓
                    ┌─────────────────────────────────┐
                    │ WebSocket Manager Service       │
                    │ - Pool Manager                  │
                    │ - 1 WS per trading pair         │
                    │ - User Data Stream (1 per user) │
                    └─────────────────────────────────┘
                                 ↓
                    ┌─────────────────────────────────┐
                    │   Binance API                   │
                    │   - REST API (rate limited)     │
                    │   - WebSocket Streams           │
                    │   - User Data Streams           │
                    └─────────────────────────────────┘
                                 ↓
                    ┌─────────────────────────────────┐
                    │   PostgreSQL Database           │
                    │   - Primary (writes)            │
                    │   - Replica (reads)             │
                    │   - Connection Pool             │
                    └─────────────────────────────────┘
```

**Improvements:**
✅ WebSocket pooling: 100 unique pairs = 100 connections (not 5000)  
✅ User Data Stream: Real-time order updates (no polling)  
✅ Redis cache: Fast API key/config access  
✅ Horizontal scaling: Add workers as needed  
✅ PostgreSQL: Handle concurrent writes  
✅ Rate limit management: Never exceed Binance limits  
✅ Connection pooling: Reuse API clients  

**Capacity:**
- Single worker: 100-200 bots
- 50 workers: 5,000-10,000 bots
- Binance WebSocket limit: 300 connections per IP
- Solution: Multiple IPs or shared connections

---

## 🎯 Key Metrics & Limits

### Binance API Limits (Spot)
- **REST API Weight**: 1200 requests/minute per IP
- **Orders**: 10 orders/second per account
- **WebSocket Connections**: 300 per IP (5 per second)
- **User Data Stream**: 1 listen key per account

### Current vs Target Performance
| Metric | Current (1-10) | Target (Phase 11) |
|--------|----------------|-------------------|
| Bots per server | 10-50 | 5,000-10,000 |
| WebSockets for 1000 bots | 1000 | 50-100 |
| Order check latency | 5 seconds (poll) | <100ms (event) |
| API requests/sec | 200+ | <50 |
| Database | SQLite (single) | PostgreSQL (pool) |
| Scalability | Vertical only | Horizontal |

### 3Commas Comparison
3Commas supports multiple exchanges and 1000s of users because they:
1. Use User Data Streams (no polling)
2. Pool WebSocket connections per trading pair
3. Run distributed worker architecture
4. Cache heavily in Redis
5. Use PostgreSQL with read replicas
6. Implement sophisticated rate limit management

**Our Phase 11 will match their architecture! 🚀**

---

## Notes
- Phase 11 is the foundation for production scale
- User Data Stream is the #1 priority (eliminates polling)
- WebSocket pooling reduces connections by 95%+
- Redis cache critical for fast bot startup
- PostgreSQL required for concurrent writes
- Horizontal scaling enables unlimited growth
- All improvements backward compatible
- Can implement incrementally (11.2 → 11.3 → 11.4 → ...)
