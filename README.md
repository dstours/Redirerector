# Redirerector
Redirerector streamlines the process of spinning up and tearing down redirector infrastructure and configuring tunnels/remote port forwarding. Currently, I've only included DigitalOcean as I wanted to build a PoC; I plan on adding Linode/others when I've got some time.

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
