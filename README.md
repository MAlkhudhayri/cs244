
README 
1. Testing Setup
Host Machine: MacBook Air (Apple Silicon, ARM64)


Virtualization: UTM with QEMU 10.0


Guest OS: Ubuntu Server 24.04.3 (ARM64)


Kernel: Linux 5.15 (supports BBR, CUBIC, Reno, and Vegas congestion control)


Resources:


Memory: 4 GB


CPU: Virtual ARM64 cores


Network: Shared Network mode (virtio-net-pci)


SSH: openssh-server installed to allow scp file transfers


2. Interfaces Used
We simulated two network types:
Wired (enp0s1)


Configured automatically by DHCP inside the VM


Used as the default interface for iPerf testing


Wireless Simulation (tc)
 Since the VM does not have a native Wi-Fi interface, we emulated wireless conditions on enp0s1 using Linux tc (Traffic Control):

 #added wireless-like delay and 1% packet loss
sudo tc qdisc add dev enp0s1 root netem delay 50ms loss 1%
#removing rule when switching back to wired
sudo tc qdisc del dev enp0s1 root netem


wired: baseline results (no tc modifications)


wlan0 simulated: added artificial delay + loss to mimic Wi-Fi


3. TCP Congestion Control Algorithms
We tested four TCP flavors available in the Linux kernel:
TCP Reno: classic loss-based algorithm


TCP CUBIC: default in modern Linux, optimized for high-speed networks


TCP Vegas: delay-based congestion control


TCP BBR: rate-based model, estimates bottleneck bandwidth


Algorithms were enabled and switched with:
#Check availability
sysctl net.ipv4.tcp_available_congestion_control

#Switch algorithm
sudo sysctl -w net.ipv4.tcp_congestion_control=<algo>

Vegas and BBR were loaded with:
sudo modprobe tcp_vegas
sudo modprobe tcp_bbr

4. Workflow for Each Run
Each experiment followed this procedure:
Switch TCP algorithm

 sudo sysctl -w net.ipv4.tcp_congestion_control= ALGORITHM_NAME

If experiment run is wireless, we simulate WiFi by running:

 sudo tc qdisc add dev enp0s1 root netem delay 50ms loss 1%

Start background pings (to log RTT/delay):

 ping -i 1 <server> > results/<ALGORITHM_NAME>_<iFace>_<LOCATION>_ping.txt &

Run iPerf3 throughput test (60 seconds):

 iperf3 -c <server> -p 5201 -t 60 -i 1 > results/<ALGORITHM_NAME>_<iFace>_<LOCATION>_iperf.txt

Log congestion window (CWND):

 ss -ti > results/<ALGORITHM_NAME>_<iFace>_<LOCATION>_cwnd.txt

Stop ping + cleanup

 sudo killall ping
# if applied (wireless)
sudo tc qdisc del dev enp0s1 root netem  
5. iPerf Servers Used
We used stable public iPerf3 servers from Clouvider (UK,US):
UK: lon.speedtest.clouvider.net


US: nyc.speedtest.clouvider.net


6. Experiment Matrix
Each TCP algorithm was tested under:
Wired (enp0s1)


Wireless-simulated (tc)


UK and US iPerf servers


This results in:
 4 algorithms × 2 interfaces × 2 locations = 16 runs
7. Output Organization
All results were saved under the results/ directory.
 Naming convention:
<algorithm>_<interface>_<location>_<metric>.txt
