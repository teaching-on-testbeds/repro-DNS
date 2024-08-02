#### Malicious client query
During the experiment, the malicious-client will issue queries that rely on the malicious referral response from the malicious-ref-server (.referral.lan domain). Queries for the .referral.lan domain should go to the resolver and the resolver should access the malicious-ref-server through the root-server.
![mal_test_route](https://github.com/user-attachments/assets/dd3f933d-37cb-4bef-b04e-06c10cc20809)
We can perform an example query for a .referral.lan name to test this resolution route.

Open eight terminal windows: SSH into the seven nodes and SSH into the resolver again in the eighth terminal.

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
sudo tcpdump -i any -s 65535 port 53 -w ~/malicious_verify
```
Next, from the malicious-client, query the resolver for the IP address of `firewall.referral.lan`. Run
```
dig firewall.referral.lan. @10.0.2.1
```
You should get a response with `10.0.0.207`&mdash;the IP address of `firewall.referral.lan`:
```
;; QUESTION SECTION:
;firewall.referral.lan.             IN      A

;; ANSWER SECTION:
firewall.referral.lan.      86400   IN      A       10.0.0.207
```
After receiving the response, stop the resolver, the servers, and the tcpdump (you can use Ctrl + C).

To view the output file from the packet capture, in the resolver terminal, run
```
tshark -r ~/malicious_verify
```
You will see the entire DNS resolution route for the IP address associated with the name `firewall.referral.lan`:
```
1   0.000000   10.0.2.200 → 10.0.2.1     DNS 106 Standard query 0x2b2b A firewall.referral.lan OPT
2   0.011873     10.0.0.1 → 10.0.0.101   DNS 84 Standard query 0x9d48 NS <Root> OPT
3   0.012299     10.0.0.1 → 10.0.0.101   DNS 90 Standard query 0x3a6b A _.lan OPT
4   0.014269   10.0.0.101 → 10.0.0.1     DNS 119 Standard query response 0x9d48 NS <Root> NS a.root-servers.net A 10.0.0.101 OPT
5   0.014430   10.0.0.101 → 10.0.0.1     DNS 131 Standard query response 0x3a6b No such name A _.lan SOA root-servers.net OPT
6   0.020878     10.0.0.1 → 10.0.0.101   DNS 103 Standard query 0xe1c9 AAAA a.root-servers.net OPT
7   0.021340     10.0.0.1 → 10.0.0.101   DNS 99 Standard query 0xda8b A _.referral.lan OPT
8   0.021686   10.0.0.101 → 10.0.0.1     DNS 126 Standard query response 0xe1c9 AAAA a.root-servers.net SOA root-servers.net OPT
9   0.021913   10.0.0.101 → 10.0.0.1     DNS 121 Standard query response 0xda8b A _.referral.lan NS ns1.referral.lan A 10.0.0.200 OPT
10   0.025186     10.0.0.1 → 10.0.0.200   DNS 106 Standard query 0xc52a A firewall.referral.lan OPT
11   0.025688     10.0.0.1 → 10.0.0.101   DNS 101 Standard query 0x49d7 AAAA ns1.referral.lan OPT
12   0.026488   10.0.0.101 → 10.0.0.1     DNS 119 Standard query response 0x49d7 AAAA ns1.referral.lan NS ns1.referral.lan A 10.0.0.200 OPT
13   0.026704     10.0.0.1 → 10.0.0.200   DNS 101 Standard query 0x1000 AAAA ns1.referral.lan OPT
14   0.027800   10.0.0.200 → 10.0.0.1     DNS 162 Standard query response 0xc52a A firewall.referral.lan A 10.0.0.207 NS ns1.referral.lan NS ns2.referral.lan A 10.0.0.200 OPT
15   0.027948   10.0.0.200 → 10.0.0.1     DNS 131 Standard query response 0x1000 AAAA ns1.referral.lan SOA ns1.referral.lan OPT
16   0.033390     10.0.2.1 → 10.0.2.200   DNS 138 Standard query response 0x2b2b A firewall.referral.lan A 10.0.0.207 OPT
```
- firewall.home.lan query from client to resolver (from ip 10.0.2.200 to ip 10.0.2.1)
- resolver query to the root server (from 10.0.0.1 to 10.0.0.101)
- root-server return the ".referral.lan" address (from 10.0.0.101 to 10.0.0.1)
- resolver query the ".referral.lan" (malicious-ref-server) address (from 10.0.0.1 to 10.0.0.200)
- malicious-ref-server return the address (10.0.0.207) for the domain name "firewall.referral.lan" (from 10.0.0.200 to 10.0.0.1)
- resolver return the address (10.0.0.207) to the client (from 10.0.2.1 to 10.0.2.200)

The address `firewall.referral.lan` is configured in the zone file of the malicious-ref-server (10.0.0.200) and this test ensures that the resolver (10.0.2.1 interface with malicious-client, 10.0.0.1 interface with servers) accesses the authoritative servers through the root (10.0.0.101).

(In our experiment, the benign-client will not issue queries for names serviced by the malicious domains, but you can still observe the resolution route by running `dig firewall.referral.lan. @10.0.1.1` from the benign-client. The only difference in the route will be the IP addresses of the client and the resolver/client interface).
