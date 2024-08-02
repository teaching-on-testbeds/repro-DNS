#### Benign client query
During the experiment, the benign client will issue queries that rely on the b-server (.benign.lan domain). Queries for the .benign.lan domain should go to the resolver and the resolver should access the benign-server through the root-server.

We can perform an example query for a .benign.lan name to test this resolution route.

Open eight terminal windows: SSH into the seven nodes and SSH into the resolver again in the eigth terminal.

To start the resolver, run
```
sudo named -g
```
And start the servers by running
```
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
on each server.

In the second resolver terminal, start a tcpdump to capture DNS traffic:
```
sudo tcpdump -i any -s 65535 port 53 -w ~/benign_verify
```
Next, from the benign-client, query the resolver for the IP address of `firewall.benign.lan`. Run
```
dig firewall.benign.lan. @10.0.1.1
```
You should get a response with `10.0.0.240`&mdash;the IP address of `firewall.benign.lan`:
```
;; QUESTION SECTION:
;firewall.benign.lan.             IN      A

;; ANSWER SECTION:
firewall.benign.lan.      86400   IN      A       10.0.0.240
```
After receiving the response, stop the resolver, the servers, and the tcpdump (you can use Ctrl + C).

To view the output file from the packet capture, in the resolver terminal, run
```
tshark -r ~/benign_verify
```
You will see the entire DNS resolution route for the IP address associated with the name `firewall.benign.lan`:
```
1   0.000000   10.0.1.100 → 10.0.1.1     DNS 106 Standard query 0x2b2b A firewall.benign.lan OPT
2   0.011873     10.0.0.1 → 10.0.0.101   DNS 84 Standard query 0x9d48 NS <Root> OPT
3   0.012299     10.0.0.1 → 10.0.0.101   DNS 90 Standard query 0x3a6b A _.lan OPT
4   0.014269   10.0.0.101 → 10.0.0.1     DNS 119 Standard query response 0x9d48 NS <Root> NS a.root-servers.net A 10.0.0.101 OPT
5   0.014430   10.0.0.101 → 10.0.0.1     DNS 131 Standard query response 0x3a6b No such name A _.lan SOA root-servers.net OPT
6   0.020878     10.0.0.1 → 10.0.0.101   DNS 103 Standard query 0xe1c9 AAAA a.root-servers.net OPT
7   0.021340     10.0.0.1 → 10.0.0.101   DNS 99 Standard query 0xda8b A _.benign.lan OPT
8   0.021686   10.0.0.101 → 10.0.0.1     DNS 126 Standard query response 0xe1c9 AAAA a.root-servers.net SOA root-servers.net OPT
9   0.021913   10.0.0.101 → 10.0.0.1     DNS 121 Standard query response 0xda8b A _.benign.lan NS ns1.benign.lan A 10.0.0.100 OPT
10   0.025186     10.0.0.1 → 10.0.0.100   DNS 106 Standard query 0xc52a A firewall.benign.lan OPT
11   0.025688     10.0.0.1 → 10.0.0.101   DNS 101 Standard query 0x49d7 AAAA ns1.benign.lan OPT
12   0.026488   10.0.0.101 → 10.0.0.1     DNS 119 Standard query response 0x49d7 AAAA ns1.benign.lan NS ns1.benign.lan A 10.0.0.100 OPT
13   0.026704     10.0.0.1 → 10.0.0.100   DNS 101 Standard query 0x1000 AAAA ns1.benign.lan OPT
14   0.027800   10.0.0.100 → 10.0.0.1     DNS 162 Standard query response 0xc52a A firewall.benign.lan A 10.0.0.240 NS ns1.benign.lan NS ns2.benign.lan A 10.0.0.100 OPT
15   0.027948   10.0.0.100 → 10.0.0.1     DNS 131 Standard query response 0x1000 AAAA ns1.benign.lan SOA ns1.benign.lan OPT
16   0.033390     10.0.1.1 → 10.0.1.100   DNS 138 Standard query response 0x2b2b A firewall.benign.lan A 10.0.0.240 OPT
```
- firewall.home.lan query from client to resolver (from ip 10.0.1.100 to ip 10.0.1.1)
- resolver query to the root server (from 10.0.0.1 to 10.0.0.101)
- root-server return the ".benign.lan" address (from 10.0.0.101 to 10.0.0.1)
- resolver query the ".benign.lan" (benign-server) address (from 10.0.0.1 to 10.0.0.100)
- benign-server return the address (10.0.0.240) for the domain name "firewall.benign.lan" (from 10.0.0.100 to 10.0.0.1)
- resolver return the address (10.0.0.240) to the client (from 10.0.1.1 to 10.0.1.100)

The address `firewall.benign.lan` is configured in the zone file of the benign-server (10.0.0.100) and this test ensures that the resolver (10.0.1.1 interface with benign-client, 10.0.0.1 interface with servers) accesses the authoritative servers through the root (10.0.0.101).

(You can observe the resolution route for a benign query issued by the malicious-client by running `dig firewall.benign.lan. @10.0.2.1` from the malicious-client. The only difference in the route will be the IP addresses of the client and the resolver/client interface).
