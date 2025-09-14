# Assignment 1 
This repository contains a Python client-server system to measure OWD between two devices over a network and compare results across wired and wireless network interfaces.

## Contents

- `client.py`: UDP sender that transmits timestamped packets and performs clock synchronization
- `server.py`: UDP receiver that timestamps incoming packets and handles sync requests
- `README.md`: This file

## Quick Start

### 1. Configure Server

Edit local variables in `server.py`:
```python
PORT = 5005
BIND_IP = '0.0.0.0'  #Listen on all interfaces
LABEL = 'wired_baseline'  #Change for each test
LOG_DIR = '.'
NO_CONSOLE = False
```

Run the server:
```bash
python3 server.py
```

### 2. Configure Client

Edit local variables in `client.py`:
```python
SERVER_IP = '192.168.100.20'  #Your server IP
PORT = 5005
BIND_IP = None  #Set to specific interface IP for wired-wifi selection
INTERVAL_MS = 100  #Packet interval in milliseconds
COUNT = 300  #Number of packets to send
PACKET_SIZE = 64  #Total packet size in bytes
LABEL = 'wired_baseline'  #Match server label
SYNC_ROUNDS = 10
SYNC_INTERVAL = 15.0  #Re-sync every N seconds
LOG_DIR = '.'
```

Run the client:
```bash
python3 client.py
```

## Configuration

### Interface Selection

To test wired interface:
```python
BIND_IP = '192.168.100.15'  #Your wired interface IP
LABEL = 'wired_baseline'
```

To test WiFi interface:
```python
BIND_IP = '192.168.100.16'  #Your wifi interface IP  
LABEL = 'wifi_baseline'
```

Find your interface IPs:
```bash
# Linux/Mac:
ifconfig

# Windows:
ipconfig
```

### Test Scenarios

Baseline comparison:
```python
#Wired baseline:
BIND_IP = 'your_wired_ip'
PACKET_SIZE = 256
INTERVAL_MS = 100
LABEL = 'wired_baseline'

#WiFi baseline:
BIND_IP = 'your_wifi_ip'
PACKET_SIZE = 256
INTERVAL_MS = 100
LABEL = 'wifi_baseline'
```

Packet size effects:
```python
#Small packets:
PACKET_SIZE = 64
LABEL = 'wired_packet_low'

#Large packets:
PACKET_SIZE = 1472
LABEL = 'wired_packet_high'
```

Frequency effects:
```python
# Low frequency:
INTERVAL_MS = 500
LABEL = 'wired_freq_low'

#High frequency:
INTERVAL_MS = 20
LABEL = 'wired_freq_high'
```

## Time Synchronization

The system uses round-trip-based synchronization:

1. Client sends SYNC_PING messages to server
2. Server replies with SYNC_PONG
3. Client measures round-trip time (RTT)
4. Estimates clock offset as RTT / 2
5. Uses median of multiple samples

Configure synchronization in `client.py`:
```python
#roundtrip_sync() function:
USE_ROUNDTRIP_SYNC = True   #Enable round-trip sync
USE_ROUNDTRIP_SYNC = False  # assume perfect sync 
```

## Data Format

Client log (`client_log_*.csv`):
```csv
seq,client_send_time,offset_used,packet_size_bytes,label
1,1234567.890123456,0.010346293,64,wired_baseline
2,1234567.990234567,0.010346293,64,wired_baseline
```

Server log (`server_log_*.csv`):
```csv
seq,client_send_time,server_recv_time,client_offset_est,owd_ms,label
1,1234567.890123456,1234567.892456789,0.010346293,2.33,wired_baseline
2,1234567.990234567,1234567.992567890,0.010346293,2.33,wired_baseline
```

## How It Works

### Protocol Design
- Custom UDP protocol with magic bytes (OWD1)
- Packet types: DATA, SYNC_PING/PONG
- Binary format with network byte order
- Variable packet sizes with padding

### OWD Calculation
```
OWD = server_recv_time - (client_send_time + client_offset_est)
```

### Features
- Timeout handling for network issues
- Packet loss detection and reporting
- Graceful error handling for malformed packets
- Periodic re-synchronization during long runs



## Troubleshooting

Address already in use error:
```bash
#Find and kill process using port 5005:
lsof -i :5005
kill <PID>

#or use different port in both files:
PORT = 5006
```

No sync samples:
- Check firewall settings (ensure UDP port 5005 is open)
- Verify network connectivity (ping between client and server)
- Check server console (should show "Round-trip sync ping" messages)

Large packet loss:
- Reduce transmission rate (increase INTERVAL_MS)
- Check network capacity
- Verify interface selection (ensure BIND_IP is correct)

## Expected Results

Typical OWD values:
- Wired (Ethernet): 1-10 ms baseline, low jitter
- WiFi: 5-50 ms baseline, higher jitter and variance
- Packet size effect: +0.1ms per 100 bytes (serialization delay)
- Frequency effect: Higher rates lead to more congestion and higher OWD

->

## Expected Results

Typical OWD values:
- Wired (Ethernet): 1-10 ms baseline, low jitter
- WiFi: 5-50 ms baseline, higher jitter and variance
- Packet size effect: +0.1ms per 100 bytes (serialization delay)
- Frequency effect: Higher rates lead to more congestion and higher OWD

## Summary of Results

### Experimental Findings

Our OWD measurement system successfully captured network performance differences between wired and wireless interfaces across multiple test scenarios:

#### Clock Synchronization Challenges
- Detected large clock offsets (up to 5 hours) between client and server machines
- Wired tests required ~18,079 second offset correction
- WiFi tests required ~0.4 second offset correction
- Demonstrates the critical importance of precise time synchronization in OWD measurement

#### Network Performance Comparison

**Wired Interface Performance:**
- OWD Range: -25 to 401ms (after offset correction)
- Lower variability and more stable delays
- Packet size effects: 64-byte packets vs 1472-byte packets showed increased delay
- Consistent performance across different transmission frequencies

**WiFi Interface Performance:**
- OWD Range: -587 to 229ms (after offset correction)
- Higher variability and jitter compared to wired
- More susceptible to sync estimation errors
- Greater sensitivity to packet size and transmission frequency changes

#### Packet Loss Analysis
- All test scenarios showed very low packet loss (≤ 1.3%)
- No significant difference in loss rates between wired and WiFi
- Network reliability was excellent across all test conditions

