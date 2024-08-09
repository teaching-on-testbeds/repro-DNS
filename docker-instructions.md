# Reproducing NRDelegationAttack: a DDoS attack on DNS

<!-- start with an intro paragraph - what we'll do, what the prerequisites are -->

This experiment is a reproduction of the major claims presented in Afek
et al. \[1\] and will measure the cost of the NRDelegation
distributed-denial-of-service attack on the resolver CPU load and its
effect on benign clients.

This experiment uses two setups, one using Docker containers and one
using Virtual Machines (VMs).

You can run this experiment on Cloudlab. To reproduce this experiment on
Cloudlab, you will need an account on Cloudlab, you will need to have
joined a project, and you will need to have set up SSH access.

## Background

<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

Distributed-denial-of-service (DDoS) attacks are attacks in which a
malicious actor issues requests that consume a large amount of
resources, resulting in performance degradation and eventually denial of
service. Especially problematic are attacks when the effect of the
initial bad request is amplified and an attacker, using only few
resources, achieves a significant effect on the victim.

The Domain Name System (DNS) translates canonical names like
"google.com" into the IP addresses that applications need to connect to
the desired resource. During a DNS resolution without malicious
activity, DNS resolvers, servers between the clients and the nameservers
in the resolution process, respond to client requests by returning a
cached name-to-address mapping or by forwarding the query to the DNS
hierarchy until a resolution is reached. When a resolver's resources are
exhausted with an attacker's requests, it is unable to complete the
resolution process for legitimate clients. This kind of attack may be
used to prevent users from accessing websites and web applications.

The NRDelegationAttack reproduced in this experiment exploits mechanisms
that were introduced to mitigate a previous denial of service attack,
the NXNSAttack, to amplify the effect of the malicious NRDelegation
requests. The NXNSAttack\[2\], uses a malicious referral response with a
list of non-existent nameservers. Upon receiving the malicious response,
the resolver attempts to simultaneously resolve all names in the list.

![NXNSAttack_flow](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NXNSAttack_flow.svg)

To mitigate the effects of this attack, a referral limit and a
"DNS_ADBFIND_NOFETCH" flag were implemented.

![NXNSAttack_mitigations_flow](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NXNSAttack_mitigations_flow.svg)

The resolver starts only resolving k, the referral limit, names and if
all k attempts fail the resolution is aborted. The referral limit k = 5
for the BIND9 resolver used in this experiment, but varies for different
resolver implementations. When a resolver reaches the limit the
"DNS_ADBFIND_NOFETCH" ("No Fetch") flag is set. These mechanisms play a
key role in the success of the NRDelegationAttack.

In the NRDelegationAttack \[1\], the attacker controls a malicious
client and at least one malicious authoritative server. The malicious
authoritative server is configured with a large malicious referral
response, n = 1500 nameserver names, that delegates the resolution to a
server non-responsive to DNS requests. The attack begins with the
malicious client querying for a name that relies on the referral
response.

![NRDelegationAttack_flow1](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NRDelegationAttack_flow1.svg)

To process the referral response, the resolver looks up each of the n
names in its cache and local memory for an existing resolution, totaling
2n lookups. Next, if k \> n, the resolver turns on the "No Fetch" flag
and starts resolving k of the n names. Each such name leads the resolver
to a server that responds with the IP address of a server that is
nonresponsive to DNS queries. Upon receiving this response a restart
event is triggerd. The "No Fetch" flag is cleared because preserving it
could prevent a valid name resolution, and in parallel, the resolver 1.
restarts resolving the referral response for the next k names, while 2.
querying the received IP address and fails to get a response. The attack
will loop through the names in referral response, repeating the 2n
lookups.

![NRDelegationAttack_resolution](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/mal_resolution.svg)

The attack continues, the resolver attempting to process the referral
response in blocks of k names, until either a restart limit is reached
or a timeout occurs. The main source of the attack's resource
consumption is the repetition of the 2n lookups.

## Results

<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

The goal of the attacker is to issue queries that significantly increase
the CPU load of the resolver. The following figure shows the
instructions executed on the resolver CPU relative to the referral
response size for both NXNS-patched and non-patched BIND9 resolvers from
the original result in the paper:

![attack_cost_paper](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/attack_cost_paper.png)

As the NXNS attack mitigations empower their NRDelegationAttack, Afek et
al. \[1\] finds that a resolver patched against the NXNS attack is more
vulnerable to the attack (costs more instructions) than a non-patched
resolver implementation.

For a NXNS-patched resolver, Afek et al. \[1\] claims that if the
referral list is large, e.g 1,500 NS names, then each NRDelegationAttack
malicious query costs at least 5,600 times more CPU instructions than a
benign query, reporting 3,415,000,000 instructions for a malicious query
and around 195,000 for a benign query.

Efforts to reproduce the instructions measurement experiments recorded
2,775,000,000 instructions for a malicious query and around 200,000
instructions for a benign query on a NXNS-patched resolver.

![attack_cost\_\_docker_repro](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/attack_cost__docker_repro.png)

(The Cost(n) function was developed in Afek et al. \[1\] and predicts
the number of instructions executed during a NRDelegationAttack on
BIND9. The function depends only on the number of referrals in the
referral response.)

This experiment will measure the instructions executed for malicious and
benign queries on patched and unpatched BIND9 implementations---you
should observe around 200,000 instructions for a benign query, more than
2,000,000,000 instructions for a malicious query on the NXNS-patched
resolver, and around 200,000,000 on the NXNS-unpatched resolver.
Additionally, we will test malicious and benign queries on a resolver
patched against the NRDelegationAttack.

Afek et al. \[1\] proposed three different mitigation mechanisms. The
following figure shows the original results in the paper for the
reduction in the effect of the attack under the proposed mitigations:

![mitigations_cost_paper](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/mitigations_cost_paper.png)

Following the responsible disclosure procedure by Afek et al. \[1\],
CVE-2022-2795 \[3\] was issued and the Internet Systems Consortium
patched BIND9 against the NRDelegationAttack, limiting the number of
database lookups performed when processing delegations, in the 9.16.33
version \[4\]. The figure below encompasses the results we obtained when
reproducing the NRDelegationAttack on NXNS-patched, NXNS-unpatched, and
NRDelegation-patched resolver implementations.

![attack_cost_mitigation_repro](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/comparison_BINDv_docker_repro.png)

When analyzing the effectiveness of a DDoS attack, we are interested in
the attack's impact on throughput (the ratio of responses per second to
queries per second) between the resolver and benign clients. The
experiment will test the throughput with and without the
NRDelegationAttack.

![throughput_no_attack](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/throughput_comparison.png)

When the resolver is under attack, you should observe a significant
performance degradation: the benign client receives 0 responses per
second for its queries. Without a response, the client is unable to
connect to the requested service.

## Run my experiment using Docker containers

<!-- Get resources -->

This experiment will measure the cost of a malicious NRDelegationAttack
query in instructions executed on the resolver CPU. For this experiment,
we will use a topology of a single node:

![docker_topology](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/docker_topology.svg)

Open this profile page:
<https://www.cloudlab.us/p/PortalProfiles/small-lan>

Click "Next", then choose 1 node, select UBUNTU 20.04 as the disk image,
and check the box for "Start X11 VNC on your nodes".

![reserve_node](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/reserve_node.png)

Click "Next", then select the Cloudlab project that you are part of and
a Cloudlab cluster with available resources. Click "Next" and then
"Finish".

It will take a few minutes for your resources to be allocated. Wait
until the node has turned green with a check mark in the upper right
corner in the "Topology View" tab signaling that your node is ready for
you to log in. Then, click on "List View" to get SSH login details for
the host. Use these details to SSH into the node.

When you have logged in to your node, continue to the next section to
configure your resources.

### Configure Resources

Once you have logged into your node, run:

``` bash
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

You can verify that the Docker Engine installation was successful by
running the hello-world image:

``` bash
sudo docker run hello-world
```

If the installation is working correctly you should see:

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

To pull the docker image used in the experiment from Docker Hub run:

``` bash
sudo docker pull shanist/dnssim:1.7
```

To install tshark, run:

``` bash
sudo apt-get install -y tshark
```

We will use tshark to view network packet captures. By viewing the
captures, we can see the resolution route of queries.

The docker environment has Valgrind's callgrind tool pre-installed. This
tool records the call history among functions and will be used to record
the number of instructions executed on the r on the resolver during
queries. We will use the KCachegrind tool for viewing the results files
generated by callgrind. Run:

``` bash
sudo apt-get install -y kcachegrind
```

to install KCachegrind.

When you have finished installing the necessary software dependencies,
continue to the next section to verify your setup.

### Turn on the environment

<!-- screen session -->

This experiment requires you have 6 terminal windows open---1 terminal
will be a terminal on the host node, and 5 terminals will be docker
environment terminals. In this experiment the terminals will be referred
to as follows: - Terminal 1: Host - Terminal 2: Resolver - Terminal 3:
Root server - Terminal 4: Malicious server - Terminal 5: Client 1 -
Terminal 6: Client 2

Open 6 terminal windows, and SSH into the host node in each window.

In the Resolver terminal, run the docker interactively so you can
control the environment

``` bash
sudo docker container run --dns 127.0.0.1 --mount type=bind,source=$(eval echo ~),target=/app -it shanist/dnssim:1.7 /bin/bash
```

You will now have a terminal inside the environment.

Next, from Host terminal, run

    CONTAINER_ID=$(sudo docker container ls -q --filter ancestor=shanist/dnssim:1.7)

This creates a variable that stores the CONTAINER_ID of your docker
container. The CONTAINER_ID will be used throughout this experiment. Now
that we have the CONTAINER_ID, we can open the remaining instances of
the docker environment.

In Terminals 3-6 (Root server, Malicious server, and both clients), run

``` bash
sudo docker exec -it $CONTAINER_ID bash
```

You should now have a terminal console on the host node, and 5 consoles
in the docker environment.

First, turn on the resolver. In the Resolver terminal, run:

``` bash
cd /etc
named -g -c /etc/named.conf
```

The environment is pre-installed with Bind 9.16.6, the NXNS-patched
resolver implementation. You can view the version by running `named -v`.

Next, in the Root server terminal, run:

``` bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```

to turn on the root authoritative server.

In Malicious server terminal, run

``` bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```

to turn on the malicious authoritative server.

See the Debugging Tips section if you encountered an error when turning
on the server(s).

### Verify the setup

Now that our resolver and authoritative servers are running, we can
perform a basic test to check if the setup is ready and well configured.

In the Client 1 terminal, run

``` bash
tcpdump -i lo -s 65535 -w /app/dump port 53
```

to start a network capture of DNS traffic.

In Client 2 terminal, run

``` bash
dig firewall.home.lan
```

to query the resolver for the IP address of `firewall.home.lan`.

Check that the correct IP address (127.0.0.207) was received in
response. You should see the following sections:

    ;; QUESTION SECTION:
    ;firewall.home.lan.             IN      A

    ;; ANSWER SECTION:
    firewall.home.lan.      86400   IN      A  127.0.0.207

Stop the `tcpdump`, the resolver, and the authoritative servers (you can
use Ctrl+C in each terminal).

In the Host terminal, run

``` bash
sudo tshark -r ~/dump
```

to view the `dump` file with the results of the capture.

You should observe the whole DNS resolution route for the name
`firewall.home.lan`:

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

The address `firewall.home.lan` is configured in the zone file of the
attack server, and this test ensures that the resolver (127.0.0.1)
accesses the attack authoritative server (127.0.0.200) through the root
(127.0.0.2) and then returns the IP address to the client (127.0.0.1 -
the resolver and client have the same IP address).

We will refer to the cost of a NRDelegation query as the number of
resolver CPU instructions executed during a malicious query. The
NRDelegation attack is harmful because a single query costs
significantly more than a benign query. This experiment will measure the
cost of malicious and benign queries on a NXNS-patched resolver
(BIND9.16.6), a NXNS-unpatched resolver (BIND9.16.2), and a
NRDelegation-patched resolver (9.16.33).

### Instructions measurement experiment - NXNS-patched resolver

This experiment will measure the CPU instructions executed on a
NXNS-patched resolver (BIND9.16.6) during a malicious query compared to
a benign query. The number of instructions will be recorded by an
instance of the callgrind tool in the command to start the resolver.

Make sure the resolver is configured to use BIND9.16.6. Run `named -v`
to check the version. If the resolver is using a different version, run:

``` bash
cd /env/bind9_16_6
make install
```

to change the version to BIND9.16.6.

Turn on the resolver with Valgrind's callgrind tool by running

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nxns_patched named -g -c /etc/named.conf
```

We use `--tool=callgrind` to specify that we are using the callgrind
tool. `named` is the BIND9 service and `/etc/named.conf` is the
configuration file.

The malicious referral response should include a long list of name
servers, in order to create such a response, the
`/env/nsd_attack/home.lan.forward` zone file needs to have 1500 records
per one malicious request. From the Malicious server, run

``` bash
cp /env/nsd_attack/home.lan.forward /env/nsd_attack/home.lan.forward.back
cp /env/reproduction/home.lan.forward /env/nsd_attack
```

to load the zone file for the malicious authoritative server. Then run

``` bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```

to turn on the attack server.

In the Root server terminal, run

``` bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```

to turn on the root server

From Client 1, query the resolver with a malicious query:

``` bash
dig attack0.home.lan.
```

The malicious referral response contains 1500 records that delegate the
resolution of `attack0.home.lan` to a DNS non-responsive server. You
will not receive a resolution for the name `attack.home.lan` because the
resolver was directed to resolve the name at a server incapable of
responding to the DNS queries. Instead, you will see a message with
`status: SERVFAIL`:

    ;; Got answer:
    ;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 26296
    ;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool:

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nxns_patched named -g -c /etc/named.conf
```

Now query the resolver with a legitimate query:

``` bash
dig test.home.lan.
```

You should receive a response with the IP address of `test.home.lan`
(127.0.0.252).

    ;; QUESTION SECTION:
    ;test.home.lan.                 IN      A

    ;; ANSWER SECTION:
    test.home.lan.          86400   IN      A  127.0.0.252

After receiving the response, stop the resolver.

Next we'll copy the results files from the docker container to the host
machine. From the host, run

``` bash
sudo docker cp $CONTAINER_ID:/etc/mal_nxns_patched $(eval echo ~)/mal_nxns_patched
sudo docker cp $CONTAINER_ID:/etc/benign_nxns_patched $(eval echo ~)/benign_nxns_patched
done
```

After copying the files, run

``` bash
sudo chown $USER $(eval echo ~)/mal_nxns_patched
sudo chown $USER $(eval echo ~)/benign_nxns_patched
```

to add permissions to open the files.

In Cloudlab, open the VNC window and run

``` bash
sudo kcachegrind $(eval echo ~)/mal_nxns_patched
```

to open the malicious query results file with the KCachegrind tool. And
run

``` bash
sudo kcachegrind $(eval echo ~)/benign_nxns_patched
```

to open the benign query results file.

![interpreting_kcachegrind_output](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/interpreting_kcachegrind_output.svg)

In the KCachegrind interface, make sure the "Relative" button is
unchecked and choose the "Instructions Fetch" tab. Record the "Incl."
value of the `fctx_getaddresses` function for both results files.
Compare the results. The benign query should be around 200,000
instructions, while the malicious query should have more than
2,000,000,000.

### Instructions measurement experiment - NXNS-unpatched resolver

This experiment follows the instructions from the NXNS-patched
experiment, but uses a BIND9.16.2 resolver, which is an NXNS-unpatched
resolver.

To change the BIND9 version, run

``` bash
cd /env/bind9_16_2
make install
```

to configure the resolver to use BIND9.16.2.

Turn on the resolver with Valgrind's callgrind tool by running

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nxns_unpatched named -g -c /etc/named.conf
```

If the authoritative servers are not running, run

``` bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```

to turn on the root and run

``` bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```

to turn on the attack server. You can check if the `nsd` process is
running with the `ps aux | grep nsd` command.

From Client 1, query the resolver with a malicious query:

``` bash
dig attack0.home.lan.
```

Stop the resolver and restart it with the Valgrind tool:

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nxns_unpatched named -g -c /etc/named.conf
```

Now query the resolver with the legitimate query:

``` bash
dig test.home.lan
```

After receiving a response (IP address 127.0.0.252), stop the resolver.

Next we'll copy the results files from the docker container to the host
machine. From the host, run

``` bash
sudo docker cp $CONTAINER_ID:/etc/mal_nxns_unpatched $(eval echo ~)/mal_nxns_unpatched
sudo docker cp $CONTAINER_ID:/etc/benign_nxns_unpatched $(eval echo ~)/benign_nxns_unpatched
```

After copying the files, run

``` bash
sudo chown $USER $(eval echo ~)/mal_nxns_unpatched
sudo chown $USER $(eval echo ~)/benign_nxns_unpatched
```

to add permissions to open the files.

In Cloudlab, open the VNC window and run

``` bash
sudo kcachegrind $(eval echo ~)/mal_nxns_unpatched
```

to open the malicious query results file with the KCachegrind tool. And
run

``` bash
sudo kcachegrind $(eval echo ~)/benign_nxns_unpatched
```

to open the benign query results file.

In the KCachegrind GUI, make sure the "Relative" button is unchecked and
choose the "Instructions Fetch" tab. Record the "Incl." value of the
`fctx_getaddresses` function for both files. Compare the results. The
benign query results should be around 200,000 instructions, while the
malicious query should have around 200,000,000.

### Instructions measurement experiment - NRDelegation-patched resolver

This experiment will measure the instructions executed on a resolver
implementation (BIND9.16.33) patched against the NRDelegationAttack.

To change the BIND9 version, run

``` bash
cd /env/bind9_16_33
make install
```

to configure the resolver to use BIND9.16.33.

Turn on the resolver with Valgrind's callgrind tool by running

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nrdelegation_patched named -g -c /etc/named.conf
```

If the authoritative servers are not turned on, run

``` bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```

to turn on the root and run

``` bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```

to turn on the attack server.

From Client 1, query the resolver with a malicious query:

``` bash
dig attack0.home.lan.
```

Once the malicious name resolution fails, stop the resolver and restart
it with the Valgrind tool:

``` bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nrdelegation_patched named -g -c /etc/named.conf
```

Now query the resolver with the legitimate query:

``` bash
dig test.home.lan
```

After receiving a response (IP address 127.0.0.252), stop the resolver.

Next we'll copy the results files from the docker container to the host
machine. From the host, run

``` bash
sudo docker cp $CONTAINER_ID:/etc/mal_nrdelegation_patched $(eval echo ~)/mal_nrdelegation_patched
sudo docker cp $CONTAINER_ID:/etc/benign_nrdelegation_patched $(eval echo ~)/benign_nrdelegation_patched
```

After copying the files, run

``` bash
sudo chown $USER $(eval echo ~)/mal_nrdelegation_patched
sudo chown $USER $(eval echo ~)/benign_nrdelegation_patched
```

to add permissions to open the files.

In Cloudlab, open the VNC window and run

``` bash
sudo kcachegrind $(eval echo ~)/mal_nrdelegation_patched
```

to open the malicious query results file with the KCachegrind tool. And
run

``` bash
sudo kcachegrind $(eval echo ~)/benign_nrdelegation_patched
```

to open the benign query results file.

Make sure the "Relative" button is unchecked and choose the
"Instructions Fetch" tab. Record the "Incl." value of the
`fctx_getaddresses` function for both files. Compare the results. The
benign query results should be around 200,000 instructions, while the
malicious query should have around 10,000,000.

### Instructions measurement experiment - referral list length

So far, our experiments used a referral response list with 1500 NS names
per malicious query (i.e. the referral response delegates the resolution
of attack0.home.lan. to 1500 different NS names). We can modify the
malicious referral list size, e.g. 100, 500, 1000 records per malicious
queries, and test the cost of a malicious query.

To edit the file that generates the referral response, run:

    sudo nano /env/reproduction/genAttackers.py

and change the range in line 6 (`for i in range(1500)`) to your desired
value. Write out, exit the editor, and run:

    python /env/reproduction/genAttackers.py

to execute the updated script that generates the output file
`attackerNameServers.txt` with the referral list. Next run

    cp /env/nsd_attack/home.lan.forward.bak /env/nsd_attack/home.lan.forward
    sed -i '/ns2        IN     A    127.0.0.201/r attackerNameServers.txt' /env/nsd_attack/home.lan.forward

to update the malicious server zone file with the new referral response
list.

You now can perform the instructions measurment experiments again to
explore how the cost of a query varies with the number of referrals.
Repeat the previous steps to change the number of referrals to another
value.

After you have performed the experiments for different numbers of
referrals, you can generate a graphical representation of your data
(this step requires you to have python and matplotlib installed). Create
a .py file and copy and paste the following code into the file:

    import matplotlib.pyplot as plt

    # Generate points
    x = [0, 100, 500, 1000, 1500] # referral list lengths (modify for your values)
    nxns_patched = [] # array for nxns_patched results (nxns_patched[i] is the result for list length x[i])
    nxns_unpatched = [] # array for nxns_unpatched results
    nrdelegation_patched = [] # array for nrdelegation_patched results

    # Adjust figure size
    plt.figure(figsize=(6.75, 4.5))

    # Plot points
    plt.plot(x, nxns_patched, marker='^', linestyle='-', color='b', label = "BIND9 with NXNS patch")
    plt.plot(x, nxns_unpatched, marker='o', linestyle='-', color='gray', label = "BIND9 without NXNS patch")
    plt.plot(x, nrdelegation_patched, marker='s', linestyle='-', color='green', label = "BIND9 with NRDelegation")

    # Label x- and y-axis
    plt.xlabel("Number of Referrals", fontdict={'fontname': 'Calibri', 'fontsize': 12}, labelpad=5)
    plt.ylabel("Number of Instructions (millions)", fontdict={'fontname': 'Calibri', 'fontsize': 13}, labelpad=3) 

    # Set x-axis and y-axis limits and tick marks
    plt.xticks(range(0, 1600, 100))
    plt.yticks(range(0, 4000, 500))
    plt.xlim(0, 1500)
    plt.ylim(0, 3500)
    plt.tick_params(axis='both', which='both', length=0, pad=10)
    for tick in plt.gca().get_xticklabels() + plt.gca().get_yticklabels():
        tick.set_fontname('Calibri')
        tick.set_fontsize(11.5)
        tick.set_fontweight('normal')

    # Add grid
    plt.grid(True)

    # Annotate points 
    """ # uncomment to annotate points
    for xi, yi in zip(x, nxns_patched):
        if xi != 0 or yi != 0:
            plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(-5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='blue', boxstyle='square', linewidth=0.5, alpha=1.0))

    for xi, yi in zip(x, nxns_unpatched):
        if xi != 0 or yi != 0:
            plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(-5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='gray', boxstyle='square', linewidth=0.5, alpha=1.0))

    for xi, yi in zip(x, nrdelegation_patched):
        if xi != 0 or yi != 0:
            plt.annotate(f'{yi:,}', xy=(xi, yi), xytext=(5, 5), textcoords='offset points', ha='right', va='bottom', color='black', fontsize=10, fontname='Calibri', bbox=dict(facecolor='white', edgecolor='green', boxstyle='square', linewidth=0.5, alpha=1.0))
    """

    # Add legend
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False, prop={'family': 'Calibri', 'size': 10})
    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Generate
    plt.show()

## Notes

### Debugging Tips

<!-- debugging tips -->

-   If there is an error stating that the port is already in use when
    turning on the authoritative servers, run `ps aux | grep nsd` and
    identify the process IDs. Run `sudo kill <ID>`. Start the server
    again.
-   If you receive a `status: SERVFAIL` response when verifying the
    setup or issuing a benign query, check if the resolver and the
    authoritative servers are up. Run `ps aux | grep named` on the
    resolver; if named is not running, start the resolver with
    `sudo named -g`. Run `ps aux | grep` on each server; if no NSD
    processes are running, start the server with
    `sudo nsd -c nsd.conf -d -f nsd.db` if using the docker, and
    `sudo nsd -c /etc/nsd/nsd.conf -d -f /var/db/nsd/nsd.db` if using
    the VM setup.

### References

\[1\] Yehuda Afek, Anat Bremler-Barr, and Shani Stajnrod. 2023.
NRDelegationAttack: Complexity DDoS attack on DNS Recursive Resolvers.
In 32nd USENIX Security Symposium (USENIX Security 23), USENIX
Association, Anaheim, CA, 3187--3204. Retrieved from
<https://www.usenix.org/conference/usenixsecurity23/presentation/afek>.

\[2\] Yehuda Afek, Anat Bremler-Barr, and Lior Shafir. NXNSAttack:
Recursive DNS inefficiencies and vulnerabilities. In 29th USENIX
Security Symposium (USENIX Security 20), pages 631--648. USENIX
Association, August 2020. Retrieved from
[https://www.usenix.org/conference/usenixsecurity20/presentation/afek.](https://www.usenix.org/conference/usenixsecurity20/presentation/afek).

\[3\] Cve-2022-2795. <https://nvd.nist.gov/vuln/detail/CVE-2022-2795>.

\[4\] ISC.
<https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes>,
2022.

\[5\] Nominum. resperf(1) - Linux man page.
<https://linux.die.net/man/1/resperf>, May 2019.

\[6\] ISC. https://www.isc.org/downloads/bind, 2021.

\[7\] NLNETLABS. https://www.nlnetlabs.nl/projects/nsd/about/, 2021.
