# Reproducing NRDelegationAttack: a DDoS attack on DNS
<!-- start with an intro paragraph - what we'll do, what the prerequisites are -->

This experiment is a reproduction of the major claims presented in Afek et al. [1] and will measure the cost of the NRDelegation distributed-denial-of-service attack on the resolver CPU load and its effect on benign clients. 

This experiment uses two setups, one using Docker containers and one using Virtual Machines (VMs).

You can run this experiment on Cloudlab. To reproduce this experiment on Cloudlab, you will need an account on Cloudlab, you will need to have joined a project, and you will need to have set up SSH access.

## Background
<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

Distributed-denial-of-service (DDoS) attacks are attacks in which a malicious actor issues requests that consume a large amount of resources, resulting in performance degradation and eventually denial of service. Especially problematic are attacks when the effect of the initial bad request is amplified and an attacker, using only few resources, achieves a significant effect on the victim.

The Domain Name System (DNS) translates canonical names like "google.com" into the IP addresses that applications need to connect to the desired resource. During a DNS resolution without malicious activity, DNS resolvers, servers between the clients and the nameservers in the resolution process, respond to client requests by returning a cached name-to-address mapping or by forwarding the query to the DNS hierarchy until a resolution is reached. When a resolver's resources are exhausted with an attacker's requests, it is unable to complete the resolution process for legitimate clients. This kind of attack may be used to prevent users from accessing websites and web applications.

The NRDelegationAttack reproduced in this experiment exploits mechanisms that were introduced to mitigate a previous denial of service attack, the NXNSAttack, to amplify the effect of the malicious NRDelegation requests. The NXNSAttack[2], uses a malicious referral response with a list of non-existent nameservers. Upon receiving the malicious response, the resolver attempts to simultaneously resolve all names in the list.
<!--Figure of NXNSAttack-->
![NXNSAttack](https://github.com/user-attachments/assets/d5ca753c-3132-42e7-9d07-6ebb67d8e5ed)

To mitigate the effects of this attack, a referral limit and a “DNS_ADBFIND_NOFETCH” flag were implemented.
<!--Figure of NXNSAttack w/ mitigations-->
![NXNSAttack_mitigations](https://github.com/user-attachments/assets/ed05125c-4fd8-4db9-90db-0bef3587f1fa)
The resolver starts only resolving k, the referral limit, names and if all k attempts fail the resolution is aborted. The referral limit k = 5 for the BIND9 resolver used in this experiment, but varies for different resolver implementations. When a resolver reaches the limit the "DNS_ADBFIND_NOFETCH" ("No Fetch") flag is set. These mechanisms play a key role in the success of the NRDelegationAttack.

In the NRDelegationAttack [1], the attacker controls a malicious client and at least one malicious authoritative server. The malicious authoritative server is configured with a large malicious referral response, n = 1500 nameserver names, that delegates the resolution to a server non-responsive to DNS requests. The attack begins with the malicious client querying for a name that relies on the referral response.
![NRDelegationAttack1](https://github.com/user-attachments/assets/f41ef7c1-7915-4018-af42-5a992698b477)
To process the referral response, the resolver looks up each of the n names in its cache and local memory for an existing resolution, totalling 2n lookups. Next, if k > n, the resolver turns on the "No Fetch" flag and starts resolving k of the n names. Each such name leads the resolver to a server that responds with the IP address of a server that is nonresponsive to DNS queries. Upon receiving this response a restart event is triggerd. The "No Fetch" flag is cleared because preserving it could prevent a valid name resolution, and in parallel, the resolver 1. restarts resolving the referral response for the next k names, while 2. querying the received IP address and fails to get a response. The attack will loop through the names in referral response, repeating the 2n lookups. The following figure shows the NRDelegationAttack after a restart event, processing the next k names:
![NRDelegationAttack2](https://github.com/user-attachments/assets/ee67324c-ca8b-4c68-a458-59ad47501369)
The attack continues until either a restart limit is reached or a timeout occurs. The main source of the attack's resource consumption is the repetition of the 2n lookups.

## Results
<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

The goal of the attacker is to issue queries that significantly increase the CPU load of the resolver. The following figure shows the instructions executed on the resolver CPU relative to the referral response size for both NXNS-patched and non-patched BIND9 resolvers from the original result in the paper:

![attack_cost_paper](https://github.com/user-attachments/assets/a35ebdb7-3654-4c49-b24b-e3ca627a02a4)

As the NXNS attack mitigations empower their NRDelegationAttack, Afek et al. [1] finds that a resolver patched against the NXNS attack is more vulnerable to the attack (costs more instructions) than a non-patched resolver implementation.

For a NXNS-patched resolver, Afek et al. [1] claims that if the referral list is large, e.g 1,500 NS names, then each NRDelegationAttack malicious query costs at least 5,600 times more CPU instructions than a benign query, reporting 3,415,000,000 instructions for a malicious query and around 195,000 for a benign query. 

Efforts to reproduce the instructions measurement experiments recorded 2,775,000,000 instructions for a malicious query and around 200,000 instructions for a benign query on a NXNS-patched resolver.

![attack_cost_repro](https://github.com/user-attachments/assets/993b98a2-7da7-4241-b651-2b1acfdf4e15)

(The cost(n) function was developed in Afek et al. [1]  and predicts the number of instructions executed during a NRDelegationAttack on BIND9. The function depends only on the number of referrals in the referral response)

This experiment will measure the instructions executed for malicious and benign queries on patched and unpatched BIND9 implementations&mdash;you should observe around 200,000 instructions for a benign query, more than 2,000,000,000 instructions for a malicious query on the NXNS-patched resolver, and around 200,000,000 on the NXNS-unpatched resolver. Additionally, we will test malicious and benign queries on a resolver patched against the NRDelegationAttack.

Afek et al. [1] proposed three different mitigation mechanisms. The following figure shows the original results in the paper for the reduction in the effect of the attack under the proposed mitigations:

![mitigations_cost_paper](https://github.com/user-attachments/assets/a1aaa63c-68e4-4b52-b189-1fa4a0edc3ee)

Following the responsible disclosure procedure by Afek et al. [1], CVE-2022-2795 [3] was issued and the Internet Systems Consortium patched BIND9 against the NRDelegationAttack, limiting the number of database lookups performed when processing delegations, in the 9.16.33 version [4]. The figure below encompasses the results we obtained when reproducing the NRDelegationAttack on NXNS-patched, NXNS-unpatched, and NRDelegation-patched resolver implementations.

![attack_cost_mitigation_repro](https://github.com/user-attachments/assets/a52e7eca-ce3d-43a2-8efa-aa6d48c85a73)

When analyzing the effectiveness of a DDoS attack, we are interested in the attack's impact on resolver throughput (the ratio between resolver responses per second and received queries per second). The experiment will test resolver throughput with and without the NRDelegationAttack.

![throughput_no_attack](https://github.com/user-attachments/assets/bede7339-17f8-459e-b21b-b105c0150faf)![throughput_attack](https://github.com/user-attachments/assets/14b58229-1fa5-406a-b8df-4da5f3dc43e6)

When the resolver is under attack, you should observe a significant performance degradation: the benign client receives 0 responses per second for its queries. Without a response, the client is unable to connect to the requested service.

## Run my experiment using VMs
<!-- Get resources -->
First, reserve your resources. For this experiment, we will use a topology of a 7 nodes&mdash;a malicious client, a benign client, the resolver, two malicious authoritative servers, a benign authoritative server, and a root authoritative server. Your complete topology will be:
<!-- image of topology -->
![vm_ex_topology](https://github.com/user-attachments/assets/d3ca66b2-ef63-48ce-88ad-245ec0fef27b)

To reserve these resources on Cloudlab, open this profile page:
<!-- link to pre-established CloudLab profile -->
[https://www.cloudlab.us/p/nyunetworks/NRDelegationAttack](https://www.cloudlab.us/p/nyunetworks/NRDelegationAttack)

Click "Next", then select the Cloudlab project that you are part of and a Cloudlab cluster with available resources. Then click "Next", and "Finish".

Wait until all of the sources have turned green and have a small check mark in the top right corner of the "Topology View" tab, indicating that they are fully configured and ready to log in. Then, click on "List View" to get SSH login details for the hosts. Use these details to SSH into each.

When you have logged in to each node, continue to the next section to configure your resources.

<!-- Configure resources -->
### Configure resources
In your choice of terminal application, open a window for each of the seven nodes.

#### Client machines
The experiment will use the resperf[4] tool to send queries, both malicious and benign, at a fixed rate and track the response rate from the resolver. SSH into the malicious-client and benign-client nodes and run
```
sudo apt update
sudo apt-get install -y build-essential libssl-dev libldns-dev libck-dev libnghttp2-dev
```
```
wget https://www.dns-oarc.net/files/dnsperf/dnsperf-2.8.0.tar.gz
tar xzf dnsperf-2.8.0.tar.gz
cd dnsperf-2.8.0
```
```
./configure
```
```
make
```
```
sudo make install
```
on both client machines to install Resperf.

For the resperf tool, we need to provide input files containing a list of queries. On the malicious-client run
```
cd ~
sudo cp /local/repository/vm_experiment/reproduction/genAttackNamesToCheck.py ~
sudo cp /local/repository/vm_experiment/reproduction/genBenignNamesToCheck.py ~
python genAttackNamesToCheck.py
python genBenignNamesToCheck.py
```
to generate an `attackerNames.txt` file with a list of malicious names and a `benignNames.txt` file with a list of benign names.

And On the benign-client run
```
cd ~
sudo cp /local/repository/vm_experiment/reproduction/genBenignNamesToCheck.py ~
python genBenignNamesToCheck.py
```
to generate the `benignNames.txt` file.

#### Resolver
Next, we will install BIND9[5], an open-source implementation of the DNS protocol, on the resolver. SSH into the resolver node and run
```
git clone -b 9_16_6 https://github.com/ShaniBenAtya/bind9.git 
cd bind9 
sudo add-apt-repository ppa:kubuntu-ppa/backports; sudo apt update; sudo apt-get install -y python3 python3-ply libuv1-dev pkg-config autoconf automake libtool libssl-dev libcap-dev dbus-x11 valgrind kcachegrind
```
```
autoreconf -fi 
```
```
./configure 
```
```
make -j 4
```
```
sudo make install
```
to install BIND9.16.6. Now provide the necessary directories and configuration files by running:
```
sudo touch /usr/local/etc/named.conf
sudo cp /local/repository/vm_experiment/resolver/named.conf /usr/local/etc/named.conf
sudo touch /usr/local/etc/db.root
sudo cp /local/repository/vm_experiment/resolver/db.root /usr/local/etc/db.root
sudo mkdir -p /usr/local/var/cache/bind
cd /usr/local/etc; sudo rndc-confgen -a
```
You can verify the installation by running `named -v` and should this message:
```
BIND 9.16.6 (Stable Release)
```
We use version 9.16.6 because it is a NXNS-patched version and most vulnerable to the NRDelegationAttack.

Install tshark, with the following command:

```
sudo apt-get install -y tshark
```

Select/write `yes` when prompted. 

And finally install kcachegrind
```
#sudo snap install kcachegrind
```

#### Authoritative nameservers
The authoritative servers will use Name Server Daemon (NSD), an open-source implementation of an authoritative DNS nameserver. 

To configure the malicious referral authoritative, the authoritative server that responds to queries with the malicious referral response, SSH into the malicious-ref-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_attack/referral.lan.forward /etc/nsd/referral.lan.forward
sudo cp /local/repository/vm_experiment/nsd_attack/referral.lan.reverse /etc/nsd/referral.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_attack/nsd.conf /etc/nsd/nsd.conf
```
to move the zone and configuration files used by NSD into the correct directory. To install NSD on the server, run:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted with the following message:
```
Configuration file '/etc/nsd/nsd.conf'
 ==> File on system created by you or by a script.
 ==> File also in package provided by package maintainer.
   What would you like to do about it ?  Your options are:
    Y or I  : install the package maintainer's version
    N or O  : keep your currently-installed version
      D     : show the differences between the versions
      Z     : start a shell to examine the situation
 The default action is to keep your current version.
*** nsd.conf (Y/I/N/O/D/Z) [default=N] ? N
```
choose "N" to use the configuration file we created in the previous step. After the installation you might get the message:
```
Job for nsd.service failed because the control process exited with error code.
See "systemctl status nsd.service" and "journalctl -xe" for details.
invoke-rc.d: initscript nsd, action "start" failed.
● nsd.service - Name Server Daemon
     Loaded: loaded (/lib/systemd/system/nsd.service; disabled; vendor preset: enabled)
     Active: activating (auto-restart) (Result: exit-code) since Mon 2024-07-29 01:33:39 CDT; 37ms ago
       Docs: man:nsd(8)
    Process: 2126 ExecStart=/usr/sbin/nsd -d (code=exited, status=1/FAILURE)
   Main PID: 2126 (code=exited, status=1/FAILURE)
```
The following steps will handle the error. To finish configuring the server, add the necessary directories and permissions for NSD:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```

To configure the malicious delegation authoritative, the authoritative server that responds to queries with the IP address of a DNS non-responsive server, SSH into the malicious-del-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_attack2/delegation.lan.forward /etc/nsd/delegation.lan.forward
sudo cp /local/repository/vm_experiment/nsd_attack2/delegation.lan.reverse /etc/nsd/delegation.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_attack2/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. Next, install NSD on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.

To configure the benign server, SSH into the benign-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_benign/benign.lan.forward /etc/nsd/benign.lan.forward
sudo cp /local/repository/vm_experiment/nsd_benign/benign.lan.reverse /etc/nsd/benign.lan.reverse
sudo cp /local/repository/vm_experiment/nsd_benign/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. Install NSD on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.

And to configure the root server, SSH into the root-server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/vm_experiment/nsd_root/net.forward /etc/nsd/net.forward
sudo cp /local/repository/vm_experiment/nsd_root/net.reverse /etc/nsd/net.reverse
sudo cp /local/repository/vm_experiment/nsd_root/nsd.conf /etc/nsd/nsd.conf
```
to load the zone and configuration files into the correct directory. And install NSD on the server by running:
```
sudo apt update
sudo apt-get install -y nsd
```
When prompted about the `etc/nsd/nsd.conf` configuration file, choose 'N' to keep your currently-installed version. Once NSD is installed, run:
```
sudo mkdir -p /run/nsd /var/db/nsd
sudo touch /run/nsd/nsd.pid /var/db/nsd/nsd.db
sudo chown -R nsd:nsd /run/nsd /var/db/nsd
```
to finish the server configuration.

When you have finished installing the necessary files and software on each node, continue to the next section to verify your setup.

### Verify Setup
We can perform a basic test, issuing queries and recording the resolution route, to check if the setup is ready and well configured.

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
sudo tcpdump -i any -s 65535 port 53 -w ~/malicious_verify.pcap
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

(In our experiment, the benign-client will not issue queries for names serviced by the malicious domains, but you can still observe the resolution route by running `dig firewall.referral.lan. @10.0.1.1` from the benign-client. Reminder: You need to restart the servers and the resolver to be able to observe this! The only difference in the route will be the IP addresses of the client and the resolver/client interface. Reminder: You need to restart the servers and the resolver to be able to observe this!)

#### Benign client query
During the experiment, the benign-client will issue queries that rely on the b-server (.benign.lan domain). Queries for the .benign.lan domain should go to the resolver and the resolver should access the benign-server through the root-server.
![ben_test_route](https://github.com/user-attachments/assets/1cd4a9fc-a466-4b62-909d-fe9994bf0bf4)
We can perform an example query for a .benign.lan name to test this resolution route.

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
sudo tcpdump -i any -s 65535 port 53 -w ~/benign_verify.pcap
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
tshark -r ~/benign_verify.pcap
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

(You can observe the resolution route for a benign query issued by the malicious-client by running `dig firewall.benign.lan. @10.0.2.1` from the malicious-client. The only difference in the route will be the IP addresses of the client and the resolver/client interface. Reminder: You need to restart the servers and the resolver to be able to observe this!)

### Instructions measurement experiment - NXNS-patched resolver

We will refer to the cost of a NRDelegation query as the number of resolver CPU instructions executed during a malicious query. This experiment will measure the CPU instructions executed on a NXNS-patched resolver (BIND9.16.6) during a malicious query compared to a benign query. The number of instructions will be recorded by an instance of the callgrind tool in the command to start the resolver.

Make sure the resolver is configured to use BIND9.16.6. Run `named -v` to check the version. If the resolver is using a different version, run:
```bash
cd ~/bind9
git checkout -f 9_16_6
./configure 
make -j 4
sudo make install
```
to change the version to BIND9.16.6.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/mal_nxns_patched named -g
```
We use `--tool=callgrind` to specify that we are using the callgrind tool. `named` is the BIND9 service and `/etc/named.conf` is the configuration file.

Turn on the authoritative servers by running 
```bash
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
in each server terminal. 

From the malicious client, query the resolver (interface IP 10.0.2.1) with a malicious query:
```bash
dig attack0.referral.lan. @10.0.2.1
```
The malicious referral response contains 1500 records that delegate the resolution of `attack0.referral.lan` to a DNS non-responsive server. You will not receive a resolution for the name `attack.referral.lan` because the resolver was directed to resolve the name at a server incapable of responding to the DNS queries.

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool:
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/benign_nxns_patched named -g
```

Now, from the benign client, query the resolver with a legitimate query:
```bash
dig b0.benign.lan. @10.0.1.1
```
You should receive a response with the IP address of `b0.benign.lan` (10.0.0.110).
```
;; QUESTION SECTION:
;b0.benign.lan.                 IN      A

;; ANSWER SECTION:
b0.benign.lan.          86400   IN      A  10.0.0.110
```
After receiving the response, stop the resolver.

Pull up your Cloudlab experiment page, locate the resolver node and click on the blue gear icon to open the VNC window on the resolver node and run
```bash
sudo kcachegrind mal_nxns_patched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind benign_nxns_patched
```
to open the benign query results file.

In the KCachegrind interface, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both results files. Compare the results. The benign query should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.

### Instructions measurement experiment - NXNS-unpatched resolver

This experiment follows the instructions from the NXNS-patched experiment, but uses a BIND9.16.2 resolver, which is an NXNS-unpatched resolver, instead of a BIND9.16.6 resolver. 

To change the BIND9 version, run
```bash
cd ~/bind9
git checkout -f 9_16_2
./configure 
make -j 4
sudo make install
```
to configure the resolver to use BIND9.16.2.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/mal_nxns_unpatched named -g
```

If the authoritative servers are not running (you can check if the `nsd` process is running with the `ps aux | grep nsd` command), run 
```bash
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
in each server terminal.

From the malicious client, query the resolver (interface IP 10.0.2.1) with a malicious query:
```bash
dig attack0.referral.lan. @10.0.2.1
```
The malicious referral response contains 1500 records that delegate the resolution of `attack0.referral.lan` to a DNS non-responsive server. You will not receive a resolution for the name `attack.referral.lan` because the resolver was directed to resolve the name at a server incapable of responding to the DNS queries.

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool:
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/benign_nxns_unpatched named -g
```

Now, from the benign client, query the resolver with a legitimate query:
```bash
dig b0.benign.lan. @10.0.1.1
```
You should receive a response with the IP address of `b0.benign.lan` (10.0.0.110).
```
;; QUESTION SECTION:
;b0.benign.lan.                 IN      A

;; ANSWER SECTION:
b0.benign.lan.          86400   IN      A  10.0.0.110
```
After receiving the response, stop the resolver.

In Cloudlab, open the VNC window on the resolver node and run
```bash
sudo kcachegrind mal_nxns_unpatched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind benign_nxns_unpatched
```
to open the benign query results file.

In the KCachegrind interface, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both results files. Compare the results. The benign query should be around 200,000 instructions, while the malicious query should be around 200,000,000.

### Instructions measurement experiment - NRDelegation-patched resolver

This experiment follows the instructions from the NXNS-patched experiment, but uses a BIND9.16.33 resolver, which is a NRDelegation-patched resolver, instead of a BIND9.16.6 resolver. 

To change the BIND9 version, run
```bash
cd ~/bind9
git checkout -f 9_16_33
./configure 
make -j 4
sudo make install
```
to configure the resolver to use BIND9.16.33.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/mal_nrdelegation_patched named -g
```

If the authoritative servers are not running (you can check if the `nsd` process is running with the `ps aux | grep nsd` command), run 
```bash
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
in each server terminal.

From the malicious client, query the resolver (interface IP 10.0.2.1) with a malicious query:
```bash
dig attack0.referral.lan. @10.0.2.1
```
The malicious referral response contains 1500 records that delegate the resolution of `attack0.referral.lan` to a DNS non-responsive server. You will not receive a resolution for the name `attack.referral.lan` because the resolver was directed to resolve the name at a server incapable of responding to the DNS queries.

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool:
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=~/benign_nrdelegation_patched named -g
```

Now, from the benign client, query the resolver with a legitimate query:
```bash
dig b0.benign.lan. @10.0.1.1
```
You should receive a response with the IP address of `b0.benign.lan` (10.0.0.110).
```
;; QUESTION SECTION:
;b0.benign.lan.                 IN      A

;; ANSWER SECTION:
b0.benign.lan.          86400   IN      A  10.0.0.110
```
After receiving the response, stop the resolver.

In Cloudlab, open the VNC window on the resolver node and run
```bash
sudo kcachegrind mal_nrdelegation_patched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind benign_nrdelegation_patched
```
to open the benign query results file.

In the KCachegrind interface, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both results files. Compare the results. The benign query should be around 200,000 instructions, while the malicious query should be around 10,000,000.

### Throughput measurement experiment
The goal of the attacker during the NRDelegation is to consume resources, preventing the resolver from servicing benign clients. To observe the impact of the attack on victims, you will run two "sub"-experiments. 

The first experiment will test the effect of the attack on benign client throughput. Benign and malicious commands will be executed with an instance of the Resperf tool on the respective client. The malicious command will simulate the attacker and issue malicious queries at a fixed rate, while the benign command will issue the benign requests until failure.

The second experiment will test the throughput without any attack. Commands will be executed with the resperf tool on each client, and both the benign and malicious commands will issue benign requests.

In the following tests, the malicious user command should be run first, but ultimately in parallel, to the benign user command. 

SSH into the seven nodes.

From the resolver, run
```
sudo named -g
```
to start BIND9 on the resolver.

For each of the four authoritative servers, run
```
sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db
```
to start NSD on the servers.

From the malicious-client, run
```
resperf -d attackerNames.txt -s 10.0.2.1 -v -m 15000 -c 60 -r 0 -R -P ~/with_attack
```
where `-d attackerNames.txt` is the input file with a list of queries that rely on the malicious referral response, and these queries are sent to the resolver with IP address `-s 10.0.2.1` at a rate of `-m 15000` queries per second, for a duration of `-c 60` seconds, sending the packets in constant time after ramping up for `-r 0`seconds. The output file `with_attack` will show the results of this test.

From the benign-client machine, run
```
resperf -d benignNames.txt -s 10.0.1.1 -v -R -P ~/with_attack
```
where `-d benignNames.txt` is the input file with a list of benign names serviced by the benign-server, `-s 10.0.1.1` is the resolver IP address, and `with_attack` is the output file.

Once the commands have finished executing, stop the resolver (Ctrl + C) in order to clear the cache. Restart the resolver with `sudo named -g`.

Next, to measure the throughput without any attack, "benignNames.txt" will be used as the input file for both commands (no malicious queries will be issued).

From the malicious-client run
```
resperf -d benignNames.txt -s 10.0.2.1 -v -m 15000 -c 60 -r 0 -R -P ~/no_attack
```
and from the benign-client run
```
resperf -d benignNames.txt -s 10.0.1.1 -v -R -P ~/no_attack
```

<!-- Analyze results -->
To view the results, open only the benign-client output files from both sub-experiments (`with_attack` and `no_attack`). Compare the benign user throughput, the "actual_qps" versus the "responses_per_sec" column, between the two tests. In ideal conditions, the responses per second should match the actual queries per second. In real network conditions without any malicious actors, there might be slight variation between queries and responses per second. During the NRDelegationAttack, you should observe a degradation in the resolver throughput for benign clients, indicated by 0 responses per seconds.

## Notes

### Debugging Tips
<!-- debugging tips -->
- If there is an error stating that the port is already in use when turning on the authoritative servers, run `ps aux | grep nsd` and identify the process IDs. Run `sudo kill <ID>`. Start the server again.
- If you receive a `status: SERVFAIL` response when verifying the setup or issuing a benign query, check if the resolver and the authoritative servers are up. Run `ps aux | grep named` on the resolver; if named is not running, start the resolver with `sudo named -g`. Run `ps aux | grep` on each server; if no NSD processes are running, start the server with `sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db`.

### References

[1] Yehuda Afek, Anat Bremler-Barr, and Shani Stajnrod. 2023. NRDelegationAttack: Complexity DDoS attack on DNS Recursive Resolvers. In 32nd USENIX Security Symposium (USENIX Security 23), USENIX Association, Anaheim, CA, 3187–3204. Retrieved from [https://www.usenix.org/conference/usenixsecurity23/presentation/afek](https://www.usenix.org/conference/usenixsecurity23/presentation/afek).

[2] Yehuda Afek, Anat Bremler-Barr, and Lior Shafir. NXNSAttack: Recursive DNS inefficiencies and vulnerabilities. In 29th USENIX Security Symposium (USENIX Security 20), pages 631–648. USENIX Association, August 2020. Retrieved from [https://www.usenix.org/conference/usenixsecurity20/presentation/afek.](https://www.usenix.org/conference/usenixsecurity20/presentation/afek).

[3] Cve-2022-2795. [https://nvd.nist.gov/vuln/detail/CVE-2022-2795](https://nvd.nist.gov/vuln/detail/CVE-2022-2795).

[4] ISC. [https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes](https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes), 2022.

[5] Nominum. resperf(1) - Linux man page. [https://linux.die.net/man/1/resperf](https://linux.die.net/man/1/resperf), May 2019.
