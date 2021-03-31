#!/usr/bin/python3
import requests, json, time, paramiko, random, subprocess, os, sys, string
from datetime import datetime
from Crypto.PublicKey import RSA
from os import chmod
from os import system

#create /tmp/.redirerector.out for logging
def touch(logfile, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    with os.fdopen(os.open(logfile, flags=flags, mode=mode, dir_fd=dir_fd)) as f:
        os.utime(f.fileno() if os.utime in os.supports_fd else logfile,
                dir_fd=None if os.supports_fd else dir_fd, **kwargs)

def generate_name():
    #generate timestamp for redirection creation
    dateTimeObj = datetime.now()
    timestamp = dateTimeObj.strftime("%d-%b-%Y (%H:%M)")

    #generate random name
    global redirector_name
    length = 6
    word = ""
    vowels = "aeiou"
    consonants = "".join(set(string.ascii_lowercase) - set(vowels))

    #generate 2 digit random number
    lower = 10**(2-1)
    upper = 10**2 - 1
    rn = random.randint(lower, upper)

    #create name
    for i in range(length):
        if i % 2 == 0:
            word += random.choice(consonants)
        else:
            word += random.choice(vowels)

    redirector_name = '%s%s' % (word,rn)

    print("\n%s - Building redirector: %s\n" % (timestamp,redirector_name), file=open("/tmp/.redirerector.out", "a"))
    return redirector_name

def tmux(command):
    system('tmux %s' % command)

def tmux_shell(command):
    tmux('send-keys "%s" "C-m"' % command)

# create ssh key
def generate_keys():
    global key_id
    try:
        key = RSA.generate(2048)
        content_file = open(private_key_name, 'wb')
        chmod(private_key_name, 0o600)
        content_file.write(key.exportKey('PEM'))
        pubkey = key.publickey()
        content_file = open(public_key_name, 'wb')
        content_file.write(pubkey.exportKey('OpenSSH'))
        public_key = pubkey.exportKey('OpenSSH')
        headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer %s" % do_token
                }
        data = {
                "name": redirector_name+" Key",
                "public_key": public_key
                }
        request = requests.post("https://api.digitalocean.com/v2/account/keys", headers=headers, json=data)
        response = json.loads(request.text)
        key_id = response["ssh_key"]["id"]
        print("[+] Generated SSH Key ID: %s" % (key_id), file=open("/tmp/.redirerector.out", "a"))
        return True
    except:
        print("[-] Error while generating keys", file=open("/tmp/.redirerector.out", "a"))
        return False

def deploy_instance(redirector_name):
    global droplet_ip, droplet_id
    headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % do_token
            }
    # Droplet information
    data = {
            "names": [
                redirector_name
                ],
            "region": "nyc3",
            "size": "s-1vcpu-1gb",
            "image": "ubuntu-16-04-x64",
            "ssh_keys": [
                key_id
                ],
            "backups": False,
            "ipv6": False,
            "user_data": None,
            "private_networking": None,
            "volumes": None,
            "tags": [
                redirector_tag
                ]
            }
    request = requests.post("https://api.digitalocean.com/v2/droplets", headers=headers, json=data)
    response = request.text
    
    if "created_at" in response:
        json_response = json.loads(response)
        droplet_id = json_response["droplets"][0]["id"]
        time.sleep(20)
        get_ip_request = requests.get("https://api.digitalocean.com/v2/droplets/%s" % droplet_id, headers=headers)
        json_response = json.loads(get_ip_request.text)
        ips = json_response["droplet"]["networks"]["v4"]
        for ip in ips:
            if ip["type"] == "public":
                droplet_ip = ip["ip_address"]
        time.sleep(30)
        print("[+] Successfully built redirector!", file=open("/tmp/.redirerector.out", "a"))
        print("\t[-] Hostname: %s" % (redirector_name), file=open("/tmp/.redirerector.out", "a"))
        print("\t[-] IP: %s" % (droplet_ip), file=open("/tmp/.redirerector.out", "a"))
        print("\t[-] Droplet ID: %s\n" % (droplet_id), file=open("/tmp/.redirerector.out", "a"))

        xterm="xterm -bg grey19 -fg white -fs 11 -e "
        ssh_command = ("ssh -i %s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s -S /tmp/.ssh_redirector -M" % (private_key_name,droplet_ip))
        print("To connect via SSH:\n%s" % (ssh_command), file=open("/tmp/.redirerector.out", "a"))
        pane_title = 'root@'+droplet_ip
        tmux('select-window -t redirerector:tool')
        tmux('select-pane -t 0.1 -T \''+pane_title+'\'')
        tmux('select-pane -t 1')
        tmux_shell(ssh_command)

def build_droplet():
    if generate_keys():
        if redirector_name:
            print("[+] Creating redirector...", file=open("/tmp/.redirerector.out", "a"))
            deploy_instance(redirector_name)

def destroy_redirectors(redirector_tag):
    print("\n[!] Deleting redirectors with tag \""+redirector_tag+"\"...", file=open("/tmp/.redirerector.out", "a"))
    headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % do_token
            }
    request = requests.delete("https://api.digitalocean.com/v2/droplets?tag_name="+redirector_tag, headers=headers)
    
    if request.text:
        response = json.loads(request.text)
        print('Successfully deleted redirectors.')
        print(response)
    else:
        print('No redirectors found.')

def build_tunnels():
    global ssh_command
    if droplet_ip is not None:
        print("\n[!] Configuring tunnels...", file=open("/tmp/.redirerector.out", "a"))
        ssh_command = ("ssh -i %s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s" % (private_key_name,droplet_ip))
        
        def sshuttle():
            print("\t[+] sshuttle connection successful.", file=open("/tmp/.redirerector.out", "a"))
            tunnel_command = ("sshuttle --dns -vr root@%s -x %s 0/0 --ssh-cmd '" % (droplet_ip,droplet_ip))
            tunnel_command += ("ssh -i %s -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -S /tmp/.sshuttle_tun -M'" % private_key_name)
            
            #set tmux title
            sshuttle_pane_title = 'SSHUTTLE '+droplet_ip
            tmux('select-window -t redirerector:networking')
            tmux('select-pane -t 0 -T \''+sshuttle_pane_title+'\'')
            tmux('select-pane -t 0')
            tmux_shell(tunnel_command)
            
        def ssh_forward():
            print("\t[+] Remote port forwarding %s:18080 -> L:8080" % (droplet_ip), file=open("/tmp/.redirerector.out", "a"))
            port_forward_command = ("ssh -R 18080:localhost:8080 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@%s -i %s -N -v -v -S /tmp/.ssh_forward -M" % (droplet_ip,private_key_name))
        
            ssh_forwarding_title = droplet_ip+':18080 -> L:8080'
            tmux('select-pane -t 1 -T \''+ssh_forwarding_title+'\'')
            tmux('select-pane -t 1')
            tmux_shell(port_forward_command)
        
        sshuttle()
        ssh_forward()
        tmux('select-window -t redirerector:tool')
        tmux('select-pane -t 1')
    else:
        input("Please create a redirector first. Enter any key to try again..")
      
def destroy_tunnels():
    print("\n[!] Destroying tunnels...\n\t[+] sshuttle\n\t[+] ssh port forwarding", file=open("/tmp/.redirerector.out", "a"))
    tmux('select-window -t redirerector:tool')
    tmux('select-pane -t 2')
    
    #destroy sshuttle
    destroy_sshuttle_cmd = "ssh -S /tmp/.sshuttle_tun -O exit sshuttle_tun"
    tmux_shell(destroy_sshuttle_cmd)
    
    #destroy sshuttle
    destroy_ssh_forwarding_cmd = "ssh -S /tmp/.ssh_forward -O exit ssh_forward"
    tmux_shell(destroy_ssh_forwarding_cmd)
    
    #destroy ssh connection to redirector
    destroy_redirector_ssh = "ssh -S /tmp/.ssh_redirector -O exit ssh_redirector"
    tmux_shell(destroy_redirector_ssh)
    
def packet_capture():
    tmux('select-window -t redirerector:networking')
    tmux('select-pane -t 2')
    interface = "eth0" or input("Interface you want to capture? ")
    tcpdump_command = ("sudo tcpdump -i %s port not 22 and host 10.10.2.164" % (interface))
    tmux_shell(tcpdump_command)

def install_deps():
    tmux('select-window -t redirerector:tool')
    print("\n[!] Installing Dependencies...\n\t[+] Updates\n\t[+] ffuf\n\t[+] seclists", file=open("/tmp/.redirerector.out", "a"))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(droplet_ip, port=22, username='root', key_filename=private_key_name)
        install_deps = "apt update ; apt -y upgrade ; cd /tmp ; wget https://github.com/ffuf/ffuf/releases/download/v1.2.1/ffuf_1.2.1_linux_amd64.tar.gz ; tar -xzf ffuf_1.2.1_linux_amd64.tar.gz ; mv ffuf /usr/local ; echo 'export PATH=$PATH:/usr/local' >> ~/.profile ; source ~/.profile ; apt install unzip -y"
        stdin, stdout, stderr = ssh.exec_command(install_deps)
        results = stdout.readlines()

        print('\n[+] Updated and installed ffuf successfully; grabbing seclists...', file=open("/tmp/.redirerector.out", "a"))
        install_seclists = "wget -c https://github.com/danielmiessler/SecLists/archive/master.zip -O /tmp/seclists.zip && unzip -o -d /usr/share/seclists /tmp/seclists.zip"
        stdin, stdout, stderr = ssh.exec_command(install_seclists)
        results = stdout.readlines()
        
    except:
        print("\n[-] Unable to install dependencies.", file=open("/tmp/.redirerector.out", "a"))
    
    tmux('select-window -t redirerector:tool')
    tmux('select-pane -t 1')
    tmux_shell('source ~/.profile')
    
    print("\t[+] Dependencies successfully installed.", file=open("/tmp/.redirerector.out", "a"))
    print("\nExample: To use ffuf on vps:\nffuf -w  /usr/share/seclists/SecLists-master/Discovery/Web-Content/common.txt -u https://DOMAIN/FUZZ -H \"User-Agent: Mozilla/5.0 Windows NT 10.0 Win64 AppleWebKit/537.36 Chrome/69.0.3497.100\" -H \"X-Forwarded-For: 127.0.0.1\" -replay-proxy http://127.0.0.1:18080", file=open("/tmp/.redirerector.out", "a"))

def get_menu_choice():
    def kill_tmux_session():
        kill_tmux = "xterm -bg grey19 -fg white -fs 11 -e 'tmux kill-session -t redirerector'"
        subprocess.Popen(kill_tmux,shell=True)
        print("[!] Successfully killed redirerector tmux session.", file=open("/tmp/.redirerector.out", "a"))
        sys.exit(0)
        
    def print_menu():
        banner = ("""\n\
    ____           ___                          __                        
   / __ \___  ____/ (_)_______  ________  _____/ /_____  _____            
  / /_/ / _ \/ __  / / ___/ _ \/ ___/ _ \/ ___/ __/ __ \/ ___/            
 / _, _/  __/ /_/ / / /  /  __/ /  /  __/ /__/ /_/ /_/ / /                
/_/ |_|\___/\__,_/_/_/   \___/_/   \___/\___/\__/\____/_/      
        """)
        os.system("clear")
        print(banner)
        print(30 * "-")
        print('1. Build redirector and setup tunnels.')
        print('2. Install Dependencies. (ffuf, seclists)')
        print('3. Destroy and rebuild redirector.')
        print('4. Start tcpdump.')
        print('9. Destroy tunnels, redirectors, tmux, and exit.')
        print(30 * "-")
    
    while True:
        print_menu()
        choice = input("Enter your choice [1-9]: ")
        if choice == '1': #build redirector
            generate_name()
            build_droplet()
            build_tunnels()
        elif choice == '2': #install dependencies
            install_deps()
        elif choice == '3': #destroy and rebuild
            confirm = input("Are you sure you want to get a new redirector [y/n]? ")
            if confirm == 'y':
                destroy_tunnels()
                destroy_redirectors(redirector_tag)
                generate_name()
                build_droplet()
                build_tunnels()
            else:
                input("Select a new menu option.")
        elif choice == '4':  #tcpdump
            packet_capture()
        elif choice == '9': #destroy tunnels, redirectors, tmux
            confirm_quit = input("Are you sure you want to destroy your redirector and exit? [y/n]? ")
            if confirm_quit == 'y':
                destroy_tunnels()
                destroy_redirectors(redirector_tag)
                kill_tmux_session()
            else:
                input("Select a new menu option.")
        else:
            input("Wrong menu selection. Enter any key to try again..")
    return [int_choice, choice]

if __name__ == "__main__":
    if os.environ.get('DISPLAY'):
        logfile = '/tmp/.redirerector.out' 
        with open(logfile,'w'): pass
        touch(logfile)
        
        #intial config
        public_key_name = "/tmp/ssh.pub"
        private_key_name = "/tmp/ssh.key"
        do_token = "" or input("Enter DigitalOcean API token: ")
        key_id = ""
        droplet_ip = None
        redirector_tag = "redirerector"
        
        #build tmux config
        tmconfig = " \
            tmux set-option -g allow-rename off; \
            tmux new -A -s redirerector -n tool -d 'tail -F /tmp/.redirerector.out'; \
            tmux split-window -v; \
            tmux select-window -t redirerector:tool; \
            tmux select-window -t 0;\
            tmux select-pane -t 0; \
            tmux split-window -v; \
            tmux new-window -n 'networking'; \
            tmux select-window -t networking; \
            tmux split-window -v; \
            tmux split-window -v; \
            tmux select-window -t redirerector:tool; \
            tmux select-pane -t 0.0 -T 'LOG'; \
            tmux select-pane -t 0.2 -T 'LOCAL';"      

        subprocess.Popen(tmconfig,shell=True).communicate()

        #launch new window for tmux
        start_tmux = "xterm -bg grey19 -fg white -fs 11 -e 'tmux a -t redirerector'"
        subprocess.Popen(start_tmux,shell=True)
        print(get_menu_choice())
    else:
        print('Please install xterm; this script will launch a new xterm window/tmux to keep things organized.')
