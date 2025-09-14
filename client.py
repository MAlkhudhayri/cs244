#!/usr/bin/env python3

import argparse
import socket
import struct
import time
import csv
import os
import statistics

MAGIC = b'OWD1'
TYPE_DATA = 1
TYPE_SYNC_REQ = 2
TYPE_SYNC_REPLY = 3

DATA_FMT = '!4sB I d d' 
SYNC_REQ_FMT = '!4sB I d' 
SYNC_REPLY_FMT = '!4sB I d d d'  

def roundtrip_sync(sock, server_addr, rounds=5, timeout=1.0):
    USE_ROUNDTRIP_SYNC = True
    
    if not USE_ROUNDTRIP_SYNC:
        return 0.0, []
    
    offsets = []
    sock.settimeout(timeout)
    
    for i in range(rounds):
        t0 = time.time()
        ping_msg = f"SYNC_PING_{i}".encode()
        sock.sendto(ping_msg, server_addr)
        
        try:
            data, _ = sock.recvfrom(1024)
            t1 = time.time()
            
            if data.startswith(b"SYNC_PONG"):
                rtt = t1 - t0
                estimated_offset = rtt / 2.0
                offsets.append(estimated_offset)
                
        except socket.timeout:
            continue
        
        time.sleep(0.05) 
    
    if offsets:
        median_offset = statistics.median(offsets)
        return median_offset, [(offset, 0) for offset in offsets]  
    
    return 0.0, []

def main():
    SERVER_IP = '192.168.100.20'  
    PORT = 5005
    BIND_IP = None  
    INTERVAL_MS = 100 
    COUNT = 300  
    PACKET_SIZE = 256  
    LABEL = 'wired_baseline'  
    SYNC_ROUNDS = 10 
    SYNC_INTERVAL = 15.0  
    LOG_DIR = '.'  
    class Config:
        def __init__(self):
            self.server_ip = SERVER_IP
            self.port = PORT
            self.bind_ip = BIND_IP
            self.interval_ms = INTERVAL_MS
            self.count = COUNT
            self.packet_size = PACKET_SIZE
            self.label = LABEL
            self.sync_rounds = SYNC_ROUNDS
            self.sync_interval = SYNC_INTERVAL
            self.log_dir = LOG_DIR
    
    args = Config()

    server_addr = (args.server_ip, args.port)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if args.bind_ip:
        sock.bind((args.bind_ip, 0))
    offset_est, sync_samples = roundtrip_sync(sock, server_addr, rounds=args.sync_rounds, timeout=1.0)
    print(f"[client] Round-trip offset estimate: {offset_est*1000:.3f} ms from {len(sync_samples)} samples")

    os.makedirs(args.log_dir, exist_ok=True)
    client_log_path = os.path.join(args.log_dir, f'client_log_{args.label}.csv')
    with open(client_log_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['seq', 'client_send_time', 'offset_used', 'packet_size_bytes', 'label'])
        
        interval = args.interval_ms / 1000.0
        next_send = time.time()
        last_resync = time.time()
        header_len = struct.calcsize(DATA_FMT)
        if args.packet_size < header_len:
            raise SystemExit(f"--packet-size must be >= {header_len}; got {args.packet_size}")
        padding_len = args.packet_size - header_len
        padding = b'\x00' * padding_len

        for seq in range(1, args.count + 1):
            now = time.time()
            if args.sync_interval > 0 and (now - last_resync) >= args.sync_interval:
                new_off, samples = roundtrip_sync(sock, server_addr, rounds=5, timeout=0.6)
                if samples:
                    offset_est = new_off
                    print(f"[client] Re-sync updated offset: {offset_est*1000:.3f} ms (from {len(samples)} samples)")
                last_resync = now
         
            if now < next_send:
                time.sleep(max(0.0, next_send - now))
            client_send_time = time.time()
            pkt = struct.pack(DATA_FMT, MAGIC, TYPE_DATA, seq, client_send_time, offset_est) + padding
            sock.sendto(pkt, server_addr)
            w.writerow([seq, f"{client_send_time:.9f}", f"{offset_est:.9f}", args.packet_size, args.label])
            f.flush()
            next_send += interval

    print(f"[client] Done. Log at {client_log_path}")

if __name__ == '__main__':
    main()
