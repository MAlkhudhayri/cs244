#!/usr/bin/env python3
import argparse
import socket
import struct
import time
import csv
import os

MAGIC = b'OWD1'
TYPE_DATA = 1
TYPE_SYNC_REQ = 2
TYPE_SYNC_REPLY = 3
DATA_FMT = '!4sB I d d'  #format:magic, type, seq, client_send_time, client_offset_est
SYNC_REQ_FMT = '!4sB I d'  #format: magic, type, seq, client_t0
SYNC_REPLY_FMT = '!4sB I d d d'  #format: magic, type, seq, server_t1, server_t2, echo_client_t0
def main():
    PORT = 5005  
    BIND_IP = '0.0.0.0' 
    LABEL = 'wifi_background'
    LOG_DIR = '.' 
    NO_CONSOLE = False  
    class Config:
        def __init__(self):
            self.port = PORT
            self.bind_ip = BIND_IP
            self.label = LABEL
            self.log_dir = LOG_DIR
            self.no_console = NO_CONSOLE
    args = Config()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind_ip, args.port))
    sock.settimeout(0.5)
    os.makedirs(args.log_dir, exist_ok=True)
    server_log_path = os.path.join(args.log_dir, f'server_log_{args.label}.csv')
    with open(server_log_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['seq', 'client_send_time', 'server_recv_time', 'client_offset_est', 'owd_ms', 'label'])

        print(f"[server] Listening on {args.bind_ip}:{args.port}  (logging to {server_log_path})")
        while True:
            try:
                data, addr = sock.recvfrom(65536)
            except socket.timeout:
                continue
            recv_time = time.time()
            
            if data.startswith(b"SYNC_PING"):
                pong_msg = b"SYNC_PONG_" + data[10:]  
                sock.sendto(pong_msg, addr)
                if not args.no_console:
                    print(f"[server] Round-trip sync ping from {addr[0]}")
                continue
            
            if len(data) >= struct.calcsize('!4sB'):
                magic, ptype = struct.unpack('!4sB', data[:5])
            else:
                continue
            if magic != MAGIC:
                continue

            if ptype == TYPE_DATA:
                header_len = struct.calcsize(DATA_FMT)
                if len(data) < header_len:
                    continue
                _, _, seq, client_send_time, client_offset_est = struct.unpack(DATA_FMT, data[:header_len])
                owd = recv_time - (client_send_time + client_offset_est)
                owd_ms = owd * 1000.0
                w.writerow([seq, f"{client_send_time:.9f}", f"{recv_time:.9f}", f"{client_offset_est:.9f}", f"{owd_ms:.3f}", args.label])
                f.flush()
                if not args.no_console:
                    print(f"[server] seq={seq} OWD~{owd_ms:.2f} ms from {addr[0]}")
            elif ptype == TYPE_SYNC_REQ:
                if len(data) < struct.calcsize(SYNC_REQ_FMT):
                    continue
                _, _, seq, client_t0 = struct.unpack(SYNC_REQ_FMT, data[:struct.calcsize(SYNC_REQ_FMT)])
                t1 = recv_time
                t2 = time.time()
                reply = struct.pack(SYNC_REPLY_FMT, MAGIC, TYPE_SYNC_REPLY, seq, t1, t2, client_t0)
                sock.sendto(reply, addr)
            else:
                pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[server] Shutting down...")
