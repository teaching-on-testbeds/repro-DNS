#### Turn on the environment

<!-- screen session -->
This experiment requires you have 6 terminal windows open&mdash;1 terminal will be a terminal on the host node, and 5 terminals will be docker environment terminals. In this experiment the terminals will be referred to as follows:
- Terminal 1: Host
- Terminal 2: Resolver
- Terminal 3: Root server
- Terminal 4: Malicious server
- Terminal 5: Client 1
- Terminal 6: Client 2

Open 6 terminal windows, and SSH into the host node in each window.

In the Resolver terminal, run the docker interactively so you can control the environment
```bash
sudo docker container run --dns 127.0.0.1 --mount type=bind,source=$(eval echo ~),target=/app -it shanist/dnssim:1.7 /bin/bash
```
You will now have a terminal inside the environment. 

Next, from Host terminal, run
```
CONTAINER_ID=$(sudo docker container ls -q --filter ancestor=shanist/dnssim:1.7)
```
This creates a variable that stores the CONTAINER_ID of your docker container. The CONTAINER_ID will be used throughout this experiment. Now that we have the CONTAINER_ID, we can open the remaining instances of the docker environment.

In Terminals 3-6 (Root server, Malicious server, and both clients), run
```bash
sudo docker exec -it $CONTAINER_ID bash
```
You should now have a terminal console on the host node, and 5 consoles in the docker environment.

First, turn on the resolver. In the Resolver terminal, run:
```bash
cd /etc
named -g -c /etc/named.conf
```
The environment is pre-installed with Bind 9.16.6, the NXNS-patched resolver implementation. You can view the version by running `named -v`.

Next, in the Root server terminal, run:
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root authoritative server. 

In Malicious server terminal, run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the malicious authoritative server. 

See the Debugging Tips section if you encountered an error when turning on the server(s).

#### Verify the setup
Now that our resolver and authoritative servers are running, we can perform a basic test to check if the setup is ready and well configured.

In the Client 1 terminal, run
```bash
tcpdump -i lo -s 65535 -w /app/dump port 53
```
to start a network capture of DNS traffic.

In Client 2 terminal, run
```bash
dig firewall.home.lan
```
to query the resolver for the IP address of `firewall.home.lan `.

Check that the correct IP address (127.0.0.207) was received in response. You should see the following sections:
```
;; QUESTION SECTION:
;firewall.home.lan.             IN      A

;; ANSWER SECTION:
firewall.home.lan.      86400   IN      A  127.0.0.207
```

Stop the `tcpdump`, the resolver, and the authoritative servers (you can use Ctrl+C in each terminal).

In the Host terminal, run
```bash
sudo tshark -r ~/dump
```
to view the `dump` file with the results of the capture. 

You should observe the whole DNS resolution route for the name `firewall.home.lan`:
```
1   0.000000    127.0.0.1 → 127.0.0.1    DNS 100 Standard query 0xd6ef A firewall.home.lan OPT # firewall.home.lan query from client to resolver
2   0.014105    127.0.0.1 → 127.0.0.2    DNS 82 Standard query 0x24cc NS <Root> OPT # Resolver query to the root server
3   0.014198    127.0.0.2 → 127.0.0.1    DNS 117 Standard query response 0x24cc NS <Root> NS a.root-servers.net A 127.0.0.2 OPT
4   0.014459    127.0.0.1 → 127.0.0.2    DNS 88 Standard query 0x6223 A _.lan OPT
5   0.014513    127.0.0.2 → 127.0.0.1    DNS 129 Standard query response 0x6223 No such name A _.lan SOA root-servers.net OPT
6   0.018196    127.0.0.1 → 127.0.0.2    DNS 93 Standard query 0xaf30 A _.home.lan OPT
7   0.018259    127.0.0.2 → 127.0.0.1    DNS 115 Standard query response 0xaf30 A _.home.lan NS ns1.home.lan A 127.0.0.200 OPT # Root server return the SLD address
8   0.019481    127.0.0.1 → 127.0.0.200  DNS 100 Standard query 0x5ea5 A firewall.home.lan OPT # Resolver query the SLD
9   0.019571  127.0.0.200 → 127.0.0.1    DNS 172 Standard query response 0x5ea5 A firewall.home.lan A 127.0.0.207 NS ns1.home.lan NS ns2.home.lan A 127.0.0.200 A 127.0.0.212 OPT # SLD return the address for the domain name
10   0.019837    127.0.0.1 → 127.0.0.2    DNS 95 Standard query 0x83a6 AAAA ns1.home.lan OPT
11   0.019890    127.0.0.2 → 127.0.0.1    DNS 113 Standard query response 0x83a6 AAAA ns1.home.lan NS ns1.home.lan A 127.0.0.200 OPT
12   0.020531    127.0.0.1 → 127.0.0.200  DNS 95 Standard query 0x669e AAAA ns1.home.lan OPT
13   0.020589  127.0.0.200 → 127.0.0.1    DNS 125 Standard query response 0x669e AAAA ns1.home.lan SOA ns1.home.lan OPT
14   0.021067    127.0.0.1 → 127.0.0.1    DNS 132 Standard query response 0xd6ef A firewall.home.lan A 127.0.0.207 OPT # Resolver return the address to the client
```
The address `firewall.home.lan` is configured in the zone file of the attack server, and this test ensures that the resolver (127.0.0.1) accesses the attack authoritative server (127.0.0.200) through the root (127.0.0.2) and then returns the IP address to the client (127.0.0.1 - the resolver and client have the same IP address).
