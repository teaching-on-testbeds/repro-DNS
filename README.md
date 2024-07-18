# NRDelegation: a severe complexity DDoS attack
<!-- start with an intro paragraph - what we'll do, what the prerequisites are -->

This experiment is a reproduction of the major claims presented in Afek et al. [1] and will measure the complexity of the NRDelegation distributed-denial-or-service attack and its effect on benign clients. 

These experiment uses two setups, one using Docker containers and one using Virtual Machines (VMs).

You can run this experiment on Cloudlab. To reproduce this experiment on Cloudlab, you will need an account on Cloudlab, you will need to have joined a project, and you will need to have set up SSH access.

## Background
<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

Distributed denial-of-service (DDoS) attacks are attacks in which a malicious attacker issues requests that consume a large amount of resources, resulting in performance degradation, and eventually denial of service.

The Domain Name System (DNS) translates canonical names like "google.com into the IP address that applications need to connect to the resource. DNS resolvers, servers between the clients and the nameservers, respond to DNS requests by returning a cached name-to-address mapping or by forwarding the query to the DNS hierarchy until a resolution is reached. When a resolver's resources are exhausted, it is unable to complete the resolution process for legitimate clients. This kind of attack may be used to prevent users from accessing websites and web applications.

The DDoS attack explored in this experiment involves a malicious client that also controls collaborating malicious authoritative nameservers. The malicious authoritative nameserver is configured with a malicious referral 


## Results
<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

As the NXNS attack mitigations empower their NRDelegation attack, Afek et al. [1] finds that a resolver patched against the NXNS attack is more vulnerable to the attack (costs more instructions) than a non-patched resolver implementation.

For a NXNS-patched resolver, Afek et al. [1] claims that if the referral list numbers 1,500 NS names, then each NRDelegationAttack malicious query costs at least 5,600 times more CPU instructions than a benign query, reporting 3,415,000,000 instructions for a malicious query and around 195,000 for a benign query. 

The following figure shows the instructions executed on the resolver CPU relative to referral response size for both NXNS-patched and non-patched BIND9 resolvers from the original result in the paper:
<!-- graph from paper -->
![attack_cost_paper](https://github.com/user-attachments/assets/a35ebdb7-3654-4c49-b24b-e3ca627a02a4)

Efforts to reproduce the instructions measurement experiments recorded 2,775,000,000 instructions for a malicious query and around 200,000 instructions for a benign query on a NXNS-patched resolver.
<!-- graph from my experiments -->
![attack_cost_repro](https://github.com/user-attachments/assets/993b98a2-7da7-4241-b651-2b1acfdf4e15)

(The cost(n) function was developed in Afek et al. [1]  and predicts the number of instructions executed during a NRDelegation attack on BIND9. The function depends only on the number of referrals in the referral response)

This experiment will measure the instructions executed for malicious and benign queries on patched and unpatched BIND9 implementations&mdash;you should observe around 200,000 instructions for a benign query, more than 2,000,000,000 instructions for a malicious query on the NXNS-patched resolver, and around 200,000,000 on the NXNS-unpatched resolver. Additionally, you will test malicious and benign queries on a resolver with mitigations against the NRDelegation attack.

Afek et al. [1] proposed three different mitigation mechanisms. The following figure shows the reduction in the effect of the attack under the proposed mitigations:

<!-- graph from paper of results from mitigation methods -->
![mitigations_cost_paper](https://github.com/user-attachments/assets/a1aaa63c-68e4-4b52-b189-1fa4a0edc3ee)

Following the responsible disclosure procedure by Afek et al. [1], Internet Systems Consortium patched BIND9 against the NRDelegation attack, limiting the number of database lookups performed when processing delegations in the 9.16.33 version [3]. The figure below summarizes the results obtained when reproducing the attack experiments for NXNS-patched, NXNS-unpatched, and NRDelegation-patched resolver implementations.

<!-- my results from E1, E3, and E4 -->
![attack_cost_mitigation_repro](https://github.com/user-attachments/assets/a52e7eca-ce3d-43a2-8efa-aa6d48c85a73)

When evaluating the effectiveness of a DDoS attack, we are interested in the attack's impact on benign client throughput (whether or not a benign client can access resources). The experiment will test resolver throughput with and without the NRDelegation attack. When the resolver is under attack, you should observe a significant performance degradation: the benign client does not receive responses, or receives less responses, for its queries (the queries per second outnumber the responses per second).

<!-- plot actual_qps and responses_per_second from my experiment -->

## Run my experiment section

### Using Docker containers
<!-- Get resources -->
For this experiment, we will use a topology of a single node with Ubuntu 20.04 or later.

<!-- link to CloudLab profile -->

#### Install software dependencies

When your node is ready to log in, SSH into the node and run
```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
to install Docker.

You can verify that the Docker Engine installation was successful by running the hello-world image
```bash
sudo docker run hello-world
```

To pull the docker image for the experiment from Docker Hub run
```bash
sudo docker pull shanist/dnssim:1.7
```

To install Wireshark run
```bash
sudo apt update
sudo apt-get install wireshark
```

To install Valgrind run
```bash
sudo apt update
sudo apt-get install valgrind
```
We will use Valgrind's callgrind tool to record the call history among functions during queries.

The data files generated by callgrind can be loaded into the KCachegrind tool for browsing the results. To install KCachegrind run
```bash
sudo apt update
sudo apt-get install kcachegrind
```

To install Resperf run
```bash
sudo apt update
sudo apt-get install resperf
```

<!-- Configure resources -->
#### Turning on the environment

On the node, run the docker interactively so you can control the environment
```bash
sudo docker container run --dns 127.0.0.1 --mount type=bind,source=<local_folder_path>,target=/app -it shanist/dnssim:1.7 /bin/bash
```
substituting `<local_folder_path>` with your local folder path. You will now have a terminal inside the environment.

The experiments require multiple terminals for the environment. First, from a terminal on your host machine, run
```bash
sudo docker container ls
```
and look for the docker name `shanist/dnssim:1.7` and copy the `CONTAINER ID`. Make note of the `CONTAINER ID` it will be used throughout the experiments.

Then to open another docker environment terminal run
```bash
sudo docker exec -it <CONTAINER ID> bash
```
substituting `<CONTAINER ID>` with your appropriate value. To open additional terminals, repeat this step.

Have three terminals in the Docker container open.

First, turn on the resolver (the environment is pre-installed with Bind 9.16.6). In the first terminal run
```bash
cd /etc
named -g -c /etc/named.conf
```
If there is a key-error run `rndc-confgen -a` and try to start it again. If you are getting the error: `loading configuration: Permission denied`, use the following commands to correct the error
```bash
chmod 777 /usr/local/etc/rndc.key
chmod 777 /usr/local/etc/bind.keys
```

Next, in the second terminal, run
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root authoritative server. 

In the third terminal, run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the malicious authoritative server. 

If there is an error stating that the port is already in use when turning on the authoritative servers, run `ps aux | grep nsd` and identify the process IDs. Run `kill <ID>`. Start the server again. 

Now that our resolver and authoritative servers are running, we can perform a basic test to check if the setup is ready and well configured.

Open another terminal inside the docker (`sudo docker exec -it <CONTAINER_ID>`) and run
```bash
tcpdump -i lo -s 65535 -w /app/dump
```
to start a network traffic capture.

Open another terminal inside the docker and run
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

Stop the `tcpdump`, the resolver, and the authoritative servers (you can use Ctrl+C).

In Cloudlab, open a VNC window to get a graphical user interface on the remote host. In the terminal of the VNC window, run
```bash
sudo wireshark -r /dump -Y "dns"
```
to open Wireshark and load the file `dump` from the capture, filtered for DNS traffic.

You should observe the whole DNS resolution route for the name `firewall.home.lan` requested.
- `firewall.home.lan` query from client to resolver (from 127.0.0.1 to 127.0.0.1)
- Resolver query to the root server (from 127.0.0.1 to 127.0.0.2)
- Root server return the SLD address (from 127.0.0.2 to 127.0.0.1)
- Resolver query the SLD (from 127.0.0.1 to 127.0.0.200)
- SLD return the address for the domain name (127.0.0.207)
- Resolver return the address to the client (127.0.0.207)

The address `firewall.home.lan` is configured in `/env/nsd_attack/home.lan.forward` and this test ensures that the resolver accesses the attack authoritative server through the root.

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

The malicious referral response should include a long list of name servers, in order to create such a response, the `/env/nsd_attack/home.lan.forward` zone file needs to have 1500 records per one malicious request. From another docker terminal, run
```bash
cp /env/reproduction/home.lan.forward /env/nsd_attack
```
to configure the zone file for the malicious authoritative server. 

In two more docker terminals start the root and malicious authoritative servers. Run
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root server, and run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server.

From another terminal in the docker environment, query the resolver with a malicious query:
```bash
dig attack0.home.lan
```
`attack0.home.lan` is a malicious query because the malicious server's zone file we configured earlier contains 1500 records that delegate the resolution of `attack0.home.lan` to a DNS non-responsive server. TYou will not receive a response with an ANSWER SECTION containing an IP address for `attack.home.lan` because the resolver was directed to a server incapable of responding to the resolver's requests.

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

Now query the resolver with a legitimate query:
```bash
dig test.home.lan
```
You should recieve a response with the IP address of `test.home.lan` (127.0.0.252).
```
;; QUESTION SECTION:
;test.home.lan.                 IN      A

;; ANSWER SECTION:
test.home.lan.          86400   IN      A  127.0.0.252
```
After receiving the response, stop the resolver.

Next we'll copy the results files from the docker container to the host machine.
In a docker container run `ls /etc` and look for files named `'callgrind.out.<VALGRIND_TEST_NUMBER>'`. Take note of the numbers. Now from the host, for each of the two results files, run
```bash
sudo docker cp <CONTAINER_ID>:/etc/callgrind.out.<VALGRIND_TEST_NUMBER> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
substituting `<CONTAINER_ID>`, `<local_folder_path>`, and `<VALGRIND_TEST_NUMBER>` with the appropriate values. For example
```bash
sudo docker cp 4f40415014fc:/etc/callgrind.out.2259 /users/gmcdvtt/callgrind.out.2259
```
After copying the files, run
```bash
sudo chown <USERNAME>:<GROUPNAME> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
for each file, to add permissions to open the files. You can run `whoami` to find your `<USERNAME>` and run `groups` to find your `<GROUPNAME>`.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.

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

Next we'll copy the results files from the docker container to the host.
In a docker container run `ls /etc` and look for files named `'callgrind.out.<VALGRIND_TEST_NUMBER>'`. Take note of the numbers. Now from the host, for each of the two results files, run
```bash
sudo docker cp <CONTAINER_ID>:/etc/callgrind.out.<VALGRIND_TEST_NUMBER> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
substituting `<CONTAINER_ID>`, `<local_folder_path>`, and `<VALGRIND_TEST_NUMBER>` with the appropriate values. After copying the files, run
```bash
sudo chown <USERNAME>:<GROUPNAME> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
for each file, to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have more than 200,000,000.

#### Instructions measurement experiment - NRDelegation mitigation

This experiment follows the instructions from the previous experiments, but uses a Bind 9.16.33 resolver, which is non-vulnerable to both NXNSAttack and NRDelegation attack.

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

Next we'll copy the results files from the docker container to the host.
In a docker container run `ls /etc` and look for files named `'callgrind.out.<VALGRIND_TEST_NUMBER>'`. Take note of the numbers. Now from the host, for each of the two results files, run
```bash
sudo docker cp <CONTAINER_ID>:/etc/callgrind.out.<VALGRIND_TEST_NUMBER> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
substituting `<CONTAINER_ID>`, `<local_folder_path>`, and `<VALGRIND_TEST_NUMBER>` with the appropriate values. After copying the files, run
```bash
sudo chown <USERNAME>:<GROUPNAME> <local_folder_path>/callgrind.out.<VALGRIND_TEST_NUMBER>
```
for each file, to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have around 10,000,000.

<!-- Analyze results -->

### Using VMs
<!-- Get resources -->
The docker environment was sufficient for measuring the cost of a malicious NRDelegation query. To accurately measure the attack's impact on benign client traffic, we want designated machines for each entity. For this experiment, we will use a topology of a 7 nodes&mdash;a malicious client, a benign client, the resolver, two malicious authoritative servers, a benign authoritative server, and a root authoritative server.
<!-- image of topology -->
<!-- link to CloudLab profile -->

<!-- Configure resources -->
In your choice of terminal application, open a window for each of the seven nodes.

When your nodes are ready to log in, ssh into the resolver node and run
```bash
named -g
```
to start BIND9.16.6 on the resolver. We use version 9.16.6 because it is a NXNS-patched version, most vulnerable to the NRDelegation attack, enabling us to measure the effect of the attack on benign client traffic.

For each of the four authoritative servers, ssh into the node and run 
```
cd \etc\nsd ; sudo nsd -c nsd.conf -d -f nsd.db
```

#### Throughput measurement experiment
You will run two "sub"-experiments. The first experiment will measure the effect of the attack on benign client throughput. The second experiment will measure the throughput without an attack.

Benign and malicious commands will be executed with an instance of the Resperf tool on the respective client. The malicious command will simulate the attacker and issue queries at a fixed rate, while the benign command will issue the benign user requests until failure.

In the following tests, the malicious user command should be run first, but ultimately in parallel, to the benign user command. SSH into the client nodes.

From the malicious client machine, run
```bash
resperf -d attackerNamesE2.txt -s resolver_IP -v -m 15000 -c 60 -r 0 -R -P output_file
```
where -s is the resolver IP address (replace resolver_IP with the correct address), -m is the number of QPS (15000) that are sent, -c is the duration of time (60) in which Resperf tries to send the queries, -r is the duration of time (0) in which Resperf ramps-up before sending the packets in constant time, and `output_file` is the output file name of your choice.

From the benign client machine, run
```bash
resperf -d benignNamesE2.txt -s resolver_IP -v -R -P output_file
```
substituting `resolver_IP` with the correct IP address and `output_file` with a unique file name of your choice.

The input file `attackerNamesE2.txt` contains a list of names that rely on the malicious referral response, and the malicious resperf command will issue queries to the resolver for these names. The input file `benignNamesE2.txt` contains a list of names serviced by the benign authoritative server, and the resperf command will query the resolver for these names

Next, to measure the throughput without any attack, "benignNamesE2.txt" will be used as the input file for both commands (no malicious queries will be issued).

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
To view the results, open only the benign user output files from both sub-experiments. Compare the benign user throughput, the "actual_qps" versus the "responses_per_sec" column, between the two tests. In ideal conditions, the responses per second should match the actual queries per second. In real network conditions without any malicious actors, there might be slight variation between queries and responses per second. During the NRDelegation attack, you should observe a degradation in the resolver throughput for benign clients, indicated by responses per second close to 0.

## Notes

### References

[1] Yehuda Afek, Anat Bremler-Barr, and Shani Stajnrod. 2023. NRDelegationAttack: Complexity DDoS attack on DNS Recursive Resolvers. In 32nd USENIX Security Symposium (USENIX Security 23), USENIX Association, Anaheim, CA, 3187–3204. Retrieved from [https://www.usenix.org/conference/usenixsecurity23/presentation/afek](https://www.usenix.org/conference/usenixsecurity23/presentation/afek).

[2] Yehuda Afek, Anat Bremler-Barr, and Lior Shafir. NXNSAttack: Recursive DNS inefficiencies and vulnerabilities. In 29th USENIX Security Symposium (USENIX Security 20), pages 631–648. USENIX Association, August 2020. Retrieved from [https://www.usenix.org/conference/usenixsecurity20/presentation/afek.](https://www.usenix.org/conference/usenixsecurity20/presentation/afek).

[3] ISC. [https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes](https://downloads.isc.org/isc/bind9/9.16.33/doc/arm/html/notes.html#security-fixes), 2022.
