# Reproducing NRDelegationAttack: a DDoS attack on DNS
<!-- start with an intro paragraph - what we'll do, what the prerequisites are -->

This experiment is a reproduction of the major claims presented in Afek et al. [1] and will measure the complexity of the NRDelegation distributed-denial-of-service attack and its effect on benign clients. 

This experiment uses two setups, one using Docker containers and one using Virtual Machines (VMs).

You can run this experiment on Cloudlab. To reproduce this experiment on Cloudlab, you will need an account on Cloudlab, you will need to have joined a project, and you will need to have set up SSH access.

## Background
<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

Distributed-denial-of-service (DDoS) attacks are attacks in which a malicious actor issues requests that consume a large amount of resources, resulting in performance degradation and eventually denial of service. Especially problematic are attacks when the effect of the initial bad request is amplified so an attacker, using only few resources, achieves a significant effect on the victim.

The Domain Name System (DNS) translates canonical names like "google.com" into the IP addresses that applications need to connect to the desired resource. DNS resolvers, servers between the clients and the nameservers, respond to DNS requests by returning a cached name-to-address mapping or by forwarding the query to the DNS hierarchy until a resolution is reached. When a resolver's resources are exhausted with the attacker's requests, it is unable to complete the resolution process for legitimate clients. This kind of attack may be used to prevent users from accessing websites and web applications.

A previous DDoS attack on DNS resolvers, the NXNSAttack [2], uses a malicious referral response with a list of non-existent nameservers. Upon receiving the malicious response, the resolver attempts to simultaneously resolve all names in the list.
<!--Figure of NXNSAttack-->
![NXNSAttack](https://github.com/user-attachments/assets/d5ca753c-3132-42e7-9d07-6ebb67d8e5ed)

To mitigate the effects of this attack, a referral limit and a “DNS_ADBFIND_NOFETCH” flag were implemented.
<!--Figure of NXNSAttack w/ mitigations-->
![NXNSAttack_mitigations](https://github.com/user-attachments/assets/ed05125c-4fd8-4db9-90db-0bef3587f1fa)
The resolver starts only resolving k, the referral limit, names and if all k attempts fail the resolution is aborted. The referral limit k = 5 for the BIND9 resolver used in this experiment, but varies for different resolver implementations. When a resolver reaches the limit the "DNS_ADBFIND_NOFETCH" ("No Fetch") flag is set. These mechanisms play a key role in the success of the NRDelegationAttack explored in this experiment.

In the NRDelegationAttack [1], the attacker controls a malicious client and at least one malicious authoritative server. The malicious authoritative server is configured with a large malicious referral response, n = 1500 nameserver names, that delegates the resolution to a server non-responsive to DNS requests. The attack begins with the malicious client querying for a name that relies on the referral response.
![NRDelegationAttack1](https://github.com/user-attachments/assets/f41ef7c1-7915-4018-af42-5a992698b477)
To process the referral response, the resolver looks up each of the n names in its cache for an existing resolution, totalling 2n lookups. The resolver then starts resolving k of the n names and sets the "No Fetch" flag. Each such name leads the resolver to a server that responds with a server IP address that is nonresponsive to DNS queries. Upon receiving this response the "No Fetch" flag is cleared, as a response was fetched, and the resolver restarts resolving the referral response for the next k names, while in parallel querying the received IP address and fails to get a response. The attack will loop through the names in referral response. The following figure shows the NRDelegationAttack after a restart event, processing the next k names:
![NRDelegationAttack2](https://github.com/user-attachments/assets/ee67324c-ca8b-4c68-a458-59ad47501369)
The attack continues until either a restart limit is reached or a timeout occurs. The main source of the attack's complexity and resource consumption is the repetition of the 2n cache lookups.

## Results
<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

The following figure shows the instructions executed on the resolver CPU relative to referral response size for both NXNS-patched and non-patched BIND9 resolvers from the original result in the paper:

![attack_cost_paper](https://github.com/user-attachments/assets/a35ebdb7-3654-4c49-b24b-e3ca627a02a4)

As the NXNS attack mitigations empower their NRDelegationAttack, Afek et al. [1] finds that a resolver patched against the NXNS attack is more vulnerable to the attack (costs more instructions) than a non-patched resolver implementation.

For a NXNS-patched resolver, Afek et al. [1] claims that if the referral list numbers 1,500 NS names, then each NRDelegationAttack malicious query costs at least 5,600 times more CPU instructions than a benign query, reporting 3,415,000,000 instructions for a malicious query and around 195,000 for a benign query. 

Efforts to reproduce the instructions measurement experiments recorded 2,775,000,000 instructions for a malicious query and around 200,000 instructions for a benign query on a NXNS-patched resolver.

![attack_cost_repro](https://github.com/user-attachments/assets/993b98a2-7da7-4241-b651-2b1acfdf4e15)

(The cost(n) function was developed in Afek et al. [1]  and predicts the number of instructions executed during a NRDelegationAttack on BIND9. The function depends only on the number of referrals in the referral response)

This experiment will measure the instructions executed for malicious and benign queries on patched and unpatched BIND9 implementations&mdash;you should observe around 200,000 instructions for a benign query, more than 2,000,000,000 instructions for a malicious query on the NXNS-patched resolver, and around 200,000,000 on the NXNS-unpatched resolver. Additionally, you will test malicious and benign queries on a resolver with mitigations against the NRDelegationAttack.

Afek et al. [1] proposed three different mitigation mechanisms. The following figure shows the original results in the paper for the reduction in the effect of the attack under the proposed mitigations:

![mitigations_cost_paper](https://github.com/user-attachments/assets/a1aaa63c-68e4-4b52-b189-1fa4a0edc3ee)

Following the responsible disclosure procedure by Afek et al. [1], Internet Systems Consortium patched BIND9 against the NRDelegationAttack, limiting the number of database lookups performed when processing delegations, in the 9.16.33 version [3]. The figure below encompasses the results we obtained when reproducing the NRDelegationAttack on NXNS-patched, NXNS-unpatched, and NRDelegation-patched resolver implementations.

![attack_cost_mitigation_repro](https://github.com/user-attachments/assets/a52e7eca-ce3d-43a2-8efa-aa6d48c85a73)

When analyzing the effectiveness of a DDoS attack, we are interested in the attack's impact on benign client throughput (whether or not a benign client can access resources). The experiment will test resolver throughput with and without the NRDelegationAttack.

![throughput_no_attack](https://github.com/user-attachments/assets/bede7339-17f8-459e-b21b-b105c0150faf)![throughput_attack](https://github.com/user-attachments/assets/14b58229-1fa5-406a-b8df-4da5f3dc43e6)

When the resolver is under attack, you should observe a significant performance degradation: the benign client does not receive responses, or receives less responses, for its queries (the queries per second outnumber the responses per second).

## Run my experiment

### Using Docker containers
<!-- Get resources -->
This experiment will measure the cost of a malicious NRDelegationAttack query. For this experiment, we will use a topology of a single node with Ubuntu 20.04.

Open this profile page: [https://www.cloudlab.us/p/PortalProfiles/small-lan](https://www.cloudlab.us/p/PortalProfiles/small-lan) 
Click "Next", then choose 1 node, select UBUNTU 20.04 as the disk image, and check the box for "Start X11 VNC on your nodes".
![docker_cloudlab_setup](https://github.com/user-attachments/assets/eaf86f7d-0d56-41f0-bab8-fba0ad2de335)
Click "Next", then select the Cloudlab project that you are part of and a Cloudlab cluster with available resources. Click "Next" and then "Finish".

It will take a few minutes for your resources to be allocated. Wait until the node has turned green with a check mark in the upper right corner in the "Topology View" tab signaling that your node is ready for you to log in.

#### Install software dependencies

When your node is ready to log in, SSH into the node and run
```bash
sudo apt update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
to install Docker.

You can verify that the Docker Engine installation was successful by running the hello-world image
```bash
sudo docker run hello-world
```
If the installation is working correctly you should see:
```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
c1ec31eb5944: Pull complete
Digest: sha256:1408fec50309afee38f3535383f5b09419e6dc0925bc69891e79d84cc4cdcec6
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.
```

To pull the docker image we will use for the experiment from Docker Hub run
```bash
sudo docker pull shanist/dnssim:1.7
```

To install tshark run
```bash
sudo apt-get install -y tshark
```

The data files generated by callgrind can be loaded into the KCachegrind tool for browsing the results. To install KCachegrind run
```bash
sudo apt-get install -y kcachegrind
```

<!-- Configure resources -->
#### Turning on the environment

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
This creates a variable that stores the CONTAINER_ID of your docker container. The CONTAINER_ID will be used throughout this experiment. Now that we have the CONTAINER_ID, we can open the remaining terminals in the docker environment.

In Terminals 3-6 (Root server, Malicious server, and the clients), run
```bash
sudo docker exec -it $CONTAINER_ID bash
```
You should now have a terminal console on the host node, and 5 consoles in the docker environment

First, turn on the resolver (the environment is pre-installed with Bind 9.16.6). In the Resolver terminal run
```bash
cd /etc
named -g -c /etc/named.conf
```

Next, in the Root server terminal, run
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

Check that the correct IP address was received in response. You should see the following sections:
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

You should observe the whole DNS resolution route for the name `firewall.home.lan` requested.
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
The address `firewall.home.lan` is configured in the zone file of the attack server and this test ensures that the resolver accesses the attack authoritative server through the root.

<!-- Run experiment -->
#### Instructions measurement experiment - NXNS-patched resolver

This experiment will measure the CPU instructions executed on a NXNS-patched resolver (BIND9.16.6) during a malicious query. The number of instructions will be recorded by an instance of the Valgrind tool in the command to start the resolver.

Make sure the resolver is configured to use Bind9.16.6. Run `named -v` to check the version. If the resolver is using a different version, run
```bash
cd /env/bind9_16_6
make install
```
to change the version to Bind 9.16.6.

Turn on the resolver with the Valgrind tool by running
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```
We use `--tool=callgrind` to specify that we are using the callgrind tool.

The malicious referral response should include a long list of name servers, in order to create such a response, the `/env/nsd_attack/home.lan.forward` zone file needs to have 1500 records per one malicious request. From Terminal 3 (malicious server), run
```bash
cp /env/reproduction/home.lan.forward /env/nsd_attack
```
to configure the zone file for the malicious authoritative server. Then run 
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server.

In Terminal 2 (root server), run
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root server

From Terminal 4 (client 1), query the resolver with a malicious query:
```bash
dig attack0.home.lan.
```
The malicious server's zone file we configured earlier contains 1500 records that delegate the resolution of `attack0.home.lan` to a DNS non-responsive server. You will not receive a resolution for the name `attack.home.lan` because the resolver was directed to a server incapable of responding to the resolver's requests. Instead, you will see a message with `status: SERVFAIL`:
```
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 26296
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1
```

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

Now query the resolver with a legitimate query:
```bash
dig test.home.lan.
```
You should receive a response with the IP address of `test.home.lan` (127.0.0.252).
```
;; QUESTION SECTION:
;test.home.lan.                 IN      A

;; ANSWER SECTION:
test.home.lan.          86400   IN      A  127.0.0.252
```
After receiving the response, stop the resolver.

Next we'll copy the results files from the docker container to the host machine. From Terminal 6, the host, run
```bash
FILES=$(sudo docker exec $CONTAINER_ID sh -c "ls /etc/callgrind.out.* 2>/dev/null")
for FILE in $FILES; do
  FILE_NAME=$(basename $FILE)
  sudo docker cp $CONTAINER_ID:/etc/$FILE_NAME $(eval echo ~)/$FILE_NAME
done
```
After copying the files, run
```bash
for FILE in ~/callgrind.out.*; do
  sudo chown $USER "$FILE"
done
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
for FILE in ~/callgrind.out.*; do
  sudo kcachegrind "$FILE"
done
```
to open the result files with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.

#### Instructions measurement experiment - NXNS-unpatched resolver

This experiment follows the instructions from the previous, but uses a Bind 9.16.2 resolver, which is an NXNS-unpatched resolver, instead of a Bind 9.16.6 resolver. 

To change the Bind version, run
```bash
cd /env/bind9_16_2
make install
```
to configure the resolver to use Bind 9.16.2.

Turn on the resolver with the Valgrind tool, run
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

If the root and malicious authoritative servers are no longer running, run 
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root and run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server. You can check if the nsd process is running with the `ps aux | grep nsd` command.

From another terminal in the docker environment, query the resolver with the malicious query:
```bash
dig attack0.home.lan
```

Stop the resolver and restart it with the Valgrind tool
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

Now query the resolver with the legitimate query:
```bash
dig test.home.lan
```
After receiving a response, stop the resolver.

Next we'll copy the results files from the docker container to the host machine. From Terminal 6, the host, run
```bash
FILES=$(sudo docker exec $CONTAINER_ID sh -c "ls /etc/callgrind.out.* 2>/dev/null")
for FILE in $FILES; do
  FILE_NAME=$(basename $FILE)
  sudo docker cp $CONTAINER_ID:/etc/$FILE_NAME $(eval echo ~)/$FILE_NAME
done
```
After copying the files, run
```bash
for FILE in ~/callgrind.out.*; do
  sudo chown $USER "$FILE"
done
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have around 200,000,000.

#### Instructions measurement experiment - NRDelegationAttack mitigation

This experiment follows the instructions from the previous experiments, but uses a Bind 9.16.33 resolver, which is non-vulnerable to both NXNSAttack and NRDelegationAttack.

To change the Bind version, run
```bash
cd /env/bind9_16_33
make install
```
to configure the resolver to use Bind 9.16.33.

Turn on the resolver with the Valgrind tool, run
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

If the root and malicious authoritative servers are no longer running, run 
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root and run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server.

From another terminal in the docker environment, query the resolver with the malicious query:
```bash
dig attack0.home.lan
```

Stop the resolver and restart it with the Valgrind tool
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

Now query the resolver with a legitimate query:
```bash
dig test.home.lan
```
After receiving a response, stop the resolver.

Next we'll copy the results files from the docker container to the host machine. From Terminal 6, the host, run
```bash
FILES=$(sudo docker exec $CONTAINER_ID sh -c "ls /etc/callgrind.out.* 2>/dev/null")
for FILE in $FILES; do
  FILE_NAME=$(basename $FILE)
  sudo docker cp $CONTAINER_ID:/etc/$FILE_NAME $(eval echo ~)/$FILE_NAME
done
```
After copying the files, run
```bash
for FILE in ~/callgrind.out.*; do
  sudo chown $USER "$FILE"
done
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have around 10,000,000.

<!-- Analyze results -->

### Using VMs
<!-- Get resources -->
The docker environment was sufficient for measuring the cost of a malicious query. To accurately measure the attack's impact on benign client traffic, we want designated machines for each entity. For this experiment, we will use a topology of a 7 nodes&mdash;a malicious client, a benign client, the resolver, two malicious authoritative servers, a benign authoritative server, and a root authoritative server.
<!-- image of topology -->
<!-- link to CloudLab profile -->

<!-- Configure resources -->
#### Configure resources
In your choice of terminal application, open a window for each of the seven nodes.

When your nodes are ready, SSH into the malicious client and the benign client. The experiment will use the resperf[4] tool to send queries, both malicious and benign, at a fixed rate and track the response rate from the resolver. When your nodes are ready to log in, ssh into the malicious and benign client nodes and run
```
sudo apt update
sudo apt-get install -y build-essential libssl-dev libldns-dev libck-dev libnghttp2-dev
wget https://www.dns-oarc.net/files/dnsperf/dnsperf-2.8.0.tar.gz
tar xzf dnsperf-2.8.0.tar.gz
cd dnsperf-2.8.0
./configure
make
sudo make install
```
on both client machines to install the resperf tool.

For the resperf tool, we need to provide input files containing a list of queries. On the malicious client run
```
cd ~
sudo cp /local/repository/external/dnssim/reproduction/attackerNamesE2.txt ~
sudo cp /local/repository/external/dnssim/reproduction/benignNamesE2.txt ~
```
and on the benign client run
```
cd ~
sudo cp /local/repository/external/dnssim/reproduction/benignNamesE2.txt ~
```
to generate the input files.

Next, we will configure the resolver. SSH into the resolver node and run
```
git clone -b 9_16_6 https://github.com/ShaniBenAtya/bind9.git 
cd bind9 
sudo apt update 
sudo apt-get install -y python3 python3-ply libuv1-dev pkg-config autoconf automake libtool libssl-dev libcap-dev
autoreconf -fi 
./configure 
make -j 4
sudo make install
sudo cp /local/repository/external/dnssim/named.conf /usr/local/etc
sudo cp /local/repository/external/dnssim/db.root /usr/local/etc
cd /usr/local/etc; sudo rndc-confgen -a
```
to install and configure BIND9.16.6 on the resolver. We use version 9.16.6 because it is a NXNS-patched version and most vulnerable to the NRDelegationAttack.

To configure the malicious referral authoritative, the authoritative server that responds to queries with the malicious referral response, SSH into the malicious_ref_server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/external/dnssim/nsd_attack/home.lan.forward /etc/nsd/referral.lan.forward
sudo cp /local/repository/external/dnssim/nsd_attack/home.lan.reverse /etc/nsd/referral.lan.reverse
sudo cp /local/repository/external/dnssim/nsd_attack/nsd.conf /etc/nsd/nsd.conf
sudo cp /local/repository/external/dnssim/nsd_attack/nsd.db /etc/nsd/nsd.db
```

To configure the malicious delegation authoritative, the authoritative server that responds to queries with the IP address of a DNS non-responsive server, SSH into the malicious_del_server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/external/dnssim/nsd_attack2/delegation.com.forward /etc/nsd/delegation.lan.forward
sudo cp /local/repository/external/dnssim/nsd_attack2/delegation.com.reverse /etc/nsd/delegation.lan.reverse
sudo cp /local/repository/external/dnssim/nsd_attack2/nsd.conf /etc/nsd/nsd.conf
sudo cp /local/repository/external/dnssim/nsd_attack2/nsd.db /etc/nsd/nsd.db
```
to load the zone and configuration files for the server. Install Name Server Daemon (NSD) on the server by running
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
choose "N" to use the configuration file we created in the previous step. And then run
```
sudo mkdir -p /run/nsd ; sudo chown nsd:nsd /run/nsd
```
to finish the server configuration.

To configure the benign server, SSH into the benign_server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/external/dnssim/nsd_benign/benign.lan.forward /etc/nsd/referral.lan.forward
sudo cp /local/repository/external/dnssim/nsd_benign/benign.lan.reverse /etc/nsd/benign.lan.reverse
sudo cp /local/repository/external/dnssim/nsd_benign/nsd.conf /etc/nsd/nsd.conf
sudo cp /local/repository/external/dnssim/nsd_benign/nsd.db /etc/nsd/nsd.db
```
to load the zone and configuration files for the server. Install Name Server Daemon (NSD) on the server by running
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
choose "N" to use the configuration file we created in the previous step. And then run
```
sudo mkdir -p /run/nsd ; sudo chown nsd:nsd /run/nsd
```
to finish the server configuration.

And to configure the root server, SSH into the root_server node and run:
```
sudo mkdir -p /etc/nsd
sudo cp /local/repository/external/dnssim/nsd_root/net.forward /etc/nsd/net.forward
sudo cp /local/repository/external/dnssim/nsd_root/net.reverse /etc/nsd/net.reverse
sudo cp /local/repository/external/dnssim/nsd_root/nsd.conf /etc/nsd/nsd.conf
sudo cp /local/repository/external/dnssim/nsd_root/nsd.db /etc/nsd/nsd.db
```
to load the zone and configuration files for the server. Install Name Server Daemon (NSD) on the server by running
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
choose "N" to use the configuration file we created in the previous step. And then run
```
sudo mkdir -p /run/nsd ; sudo chown nsd:nsd /run/nsd
```
to finish the server configuration.

#### Throughput measurement experiment
You will run two "sub"-experiments. The first experiment will measure the effect of the attack on benign client throughput. The second experiment will measure the throughput without an attack.

Benign and malicious commands will be executed with an instance of the Resperf tool on the respective client. The malicious command will simulate the attacker and issue queries at a fixed rate, while the benign command will issue the benign user requests until failure.

In the following tests, the malicious user command should be run first, but ultimately in parallel, to the benign user command. SSH into the client nodes.

From the resolver node, run
```bash
sudo named -g
```
to start the resolver.

For each of the four authoritative servers, run 
```
cd /etc/nsd ; sudo nsd -c nsd.conf -d -f nsd.db
```
to start the servers.

From the malicious_client machine, run
```bash
resperf -d attackerNamesE2.txt -s resolver_IP -v -m 15000 -c 60 -r 0 -R -P 
```
where -s is the resolver IP address (replace resolver_IP with the correct address), -m is the number of QPS (15000) that are sent, -c is the duration of time (60) in which Resperf tries to send the queries, -r is the duration of time (0) in which Resperf ramps-up before sending the packets in constant time, and `output_file` is the output file name of your choice.

From the benign client machine, run
```bash
resperf -d benignNamesE2.txt -s resolver_IP -v -R -P output_file
```
substituting `resolver_IP` with the correct IP address and `output_file` with a unique file name of your choice.

The input file `attackerNamesE2.txt` contains a list of names that rely on the malicious referral response, and the malicious resperf command will issue queries to the resolver for these names. The input file `benignNamesE2.txt` contains a list of names serviced by the benign authoritative server, and the resperf command will query the resolver for these names

Next, to measure the throughput without any attack, "benignNamesE2.txt" will be used as the input file for both commands (no malicious queries will be issued). To test with a clear cache stop the resolver (Ctrl+C), run `sudo rndc flush` and then restart the resolver with `named -g`.

From the malicious user run
```bash
resperf -d benignNamesE2.txt -s resolver_IP -v -m 15000 -c 60 -r 0 -R -P output_file
```
and from the benign user run
```bash
resperf -d benignNamesE2.txt -s resolver_IP -v -R -P output_file
```
substituting `resolver_IP` with the correct IP address and `output_file` with a unique file name of your choice.

<!-- Analyze results -->
To view the results, open only the benign user output files from both sub-experiments. Compare the benign user throughput, the "actual_qps" versus the "responses_per_sec" column, between the two tests. In ideal conditions, the responses per second should match the actual queries per second. In real network conditions without any malicious actors, there might be slight variation between queries and responses per second. During the NRDelegationAttack, you should observe a degradation in the resolver throughput for benign clients, indicated by responses per second close to 0.

## Notes

### Debugging Tips
<!-- debugging tips -->
If there is an error stating that the port is already in use when turning on the authoritative servers, run `ps aux | grep nsd` and identify the process IDs. Run `kill <ID>`. Start the server again. 

### References

[1] Yehuda Afek, Anat Bremler-Barr, and Shani Stajnrod. 2023. NRDelegationAttack: Complexity DDoS attack on DNS Recursive Resolvers. In 32nd USENIX Security Symposium (USENIX Security 23), USENIX Association, Anaheim, CA, 3187–3204. Retrieved from [https://www.usenix.org/conference/usenixsecurity23/presentation/afek](https://www.usenix.org/conference/usenixsecurity23/presentation/afek).

[2] Yehuda Afek, Anat Bremler-Barr, and Lior Shafir. NXNSAttack: Recursive DNS inefficiencies and vulnerabilities. In 29th USENIX Security Symposium (USENIX Security 20), pages 631–648. USENIX Association, August 2020. Retrieved from [https://www.usenix.org/conference/usenixsecurity20/presentation/afek.](https://www.usenix.org/conference/usenixsecurity20/presentation/afek).

[3] ISC. [https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes](https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes), 2022.

[4] Nominum. resperf(1) - Linux man page. [https://linux.die.net/man/1/resperf](https://linux.die.net/man/1/resperf), May 2019.

