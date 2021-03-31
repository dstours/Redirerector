# Redirerector
Redirerector automates the process of spinning up/tearing down redirector infrastructure, tunneling traffic via sshuttle, and remote port forwarding your VPS_IP:18080 to LOCAL:8080.

At this point in time DigitalOcean is only supported as I wanted to build a quick PoC; I plan on adding Linode/other VPS' as well as multi-redirector support soon. 

![ScreenShot](https://github.com/dstours/Redirerector/blob/main/screenshots/redirerector_running.png)
  
# Usage
This script utilizes xterm and tmux to keep things organized. Highly recommend installing them or things probably will not work.

To run, either copy the redirerector.py script and install paramiko and the requests libraries...(or git clone the repo).
```
git clone https://github.com/dstours/Redirerector.git
pip3 install -r requirements.txt
```

This is a work in progress.
