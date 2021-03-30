# Redirerector
Redirerector automates the process of spinning up/tearing down redirector infrastructure, tunneling traffic via sshuttle, and remote port forwarding your VPS_IP:18080 to LOCAL:8080.

At this point in time DigitalOcean is only supported as I wanted to build a quick PoC; I plan on adding Linode/other VPS' as well as multi-redirector support soon. 

```python
    ____           ___                          __                        
   / __ \___  ____/ (_)_______  ________  _____/ /_____  _____            
  / /_/ / _ \/ __  / / ___/ _ \/ ___/ _ \/ ___/ __/ __ \/ ___/            
 / _, _/  __/ /_/ / / /  /  __/ /  /  __/ /__/ /_/ /_/ / /                
/_/ |_|\___/\__,_/_/_/   \___/_/   \___/\___/\__/\____/_/      
        
------------------------------
1. Build redirector and setup tunnels.
2. Install Dependencies. (ffuf, seclists)
3. Destroy and rebuild redirector.
4. Start tcpdump.
9. Destroy tunnels, redirectors, tmux, and exit.
------------------------------
Enter your choice [1-9]:
  ```

This is a work in progress.
