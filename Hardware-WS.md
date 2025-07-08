# **Hardware WebSocket Communication Module Documentation**

## **WebSocket Endpoint**
- **URL**: `wss://api.duckycart.me:8000/ws/hardware/cartID`
- **Protocol**: WebSocket
- **Description**: Real-time communication channel for hardware cart clients.
- **cartID is integer**
---

## **Server-to-Hardware Messages**

### **1. QR Code Generation Command**
**Triggered When**: QR code endpoint is accessed to generate QR for cart

**Message Format**:
```json
{
  "type": "generate_qr",
  "data": null
}
```
**data** : null (no additional data needed)
**Sent From**: 
- Endpoint: `GET /customer-session/qr/{cart_id}`
- Function: `get_qr()`
- Timing: Before QR code generation and return

---

### **2. Session Start Command**
**Triggered When**: QR code is scanned and session is successfully created

**Message Format**:
```json
{
  "type": "session_started",
  "data": 1
}
```
**data** : sessionID for future communication
**Sent From**: 
- Function: `create_session()`
- Timing: After session record is saved to database and cart status updated to `'in_use'`

---

### **3. Payment Created Command**
**Triggered When**: Payment is successfully generated and saved to database

**Message Format**:
```json
{
  "type": "payment_created", 
  "data": 456
}
```

**Sent From**:
- Timing: After payment record is created and before client notification

---

### **4. Session End Command** 
**Triggered When**: Session is finished after successful payment completion

**Message Format**:
```json
{
  "type": "end_session",
  "data": 456
}
```

**Sent From**:
- Timing: After session is deactivated, cart status changed to `'available'`, and analytics logged

---

## **Message Delivery Flow**

### **Session Lifecycle Messages**
1. **QR Request** → `generate_qr` command sent
2. **QR Scan** → `session_started` command sent
3. **Shopping Period** → No WebSocket messages
4. **Payment Creation** → `payment_created` command sent  
5. **Payment Completion** → `end_session` command sent

---

## **Message Timing**

### **generate_qr**
- **Before**: Cart is available for session creation
- **Trigger**: Client requests QR code for cart
- **After**: QR code generated and returned to client

### **session_started**
- **Before**: Cart status = `'available'`
- **Trigger**: QR code validation successful
- **After**: Cart status = `'in_use'`, Session created, Message sent

### **payment_created**
- **Before**: Shopping complete, payment request initiated
- **Trigger**: Payment record saved successfully
- **After**: Payment URL generated, Hardware notified

### **end_session**
- **Before**: Payment processed successfully
- **Trigger**: `finish_session()` called
- **After**: Session deactivated, Cart available, Analytics logged

---

## **Hardware Expected Actions**

### **On `generate_qr`**
Hardware should prepare for QR code display (activate display, prepare for scanning, etc.)

### **On `session_started`**
Hardware should initialize shopping mode (display activation, scanner ready, etc.)

### **On `payment_created`** 
Hardware should indicate payment is ready (hold all resources and block any fraud)

### **On `end_session`**
Hardware should return to idle state (cleanup)

---

## **WebSocket Connection Requirements**

### **Connection URL**
```
wss://api.duckycart.me:8000/ws/hardware/cartID
```

### **Message Format**
- **Protocol**: JSON over WebSocket
- **Encoding**: UTF-8
- **Structure**: All messages contain `type` (command) and `data` (session_id or null) fields

### **Hardware Client Setup**
Hardware clients should:
1. Connect to WebSocket endpoint
2. Listen for incoming JSON messages
3. Parse `type` field to determine action
4. Use `data` field to get session_id for tracking (when available)
5. Register with specific cart_id for message routing