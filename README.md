<!-- start with an intro paragraph - what we'll do, what the prerequisites are -->

## Background

<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

## Results

<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

## Run my experiment section

### Using Docker containers

<!-- Get resources -->
For this experiment, we will use a topology of a single node with Ubuntu 20.04 or later.

#### Install software

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
to query the resolver.

Check that the correct IP address was received in response.
```
;; QUESTION SECTION:
;firewall.home.lan.             IN      A

;; ANSWER SECTION:
firewall.home.lan.      86400   IN      A  127.0.0.207
```

Stop the `tcpdump` (you can use Ctrl+C), the resolver, and the authoritative servers

In CloudLab, open a VNC window to get a graphical user interface on the remote host. In the terminal of the VNC window run
```bash
sudo wireshark -r /dump -Y "dns"
```
to open Wireshark and load the file `/dump` from the capture and filter DNS requests.

You should observe the whole DNS resolution route for the domain name `firewall.home.lan` requested.
- `firewall.home.lan` query from client to resolver (from 127.0.0.1 to 127.0.0.1)
- Resolver query to the root server (from 127.0.0.1 to 127.0.0.2)
- Root server return the SLD address (from 127.0.0.2 to 127.0.0.1)
- Resolver query the SLD (from 127.0.0.1 to 127.0.0.200)
- SLD return the address for the domain name (127.0.0.207)
- Resolver return the address to the client (127.0.0.207)

The address `firewall.home.lan` is configured in `/env/nsd_attack/home.lan.forward` and this test ensures that the resolver accesses the attack authoritative server through the root.

<!-- Run experiment -->
#### (E1) Instructions measurement experiment

Make sure the resolver is configured to use Bind 9.16.6. To check the version run
```bash
named -v
```
If the resolver is using a different version, run
```bash
cd /env/bind9_16_6
make install
```
to change the version to Bind 9.16.6

Turn on the resolver with the Valgrind tool by running
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```
We use `--tool=callgrind` to specify that we are using the callgrind tool.

The malicious referral response should include a long list of name servers, in order to create such a list the `/env/nsd_attack/home.lan.forward` zone file needs to have 1500 records per one malicious request. From another docker terminal, run
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

Stop the resolver and restart it with the Valgrind tool
```bash
cd /etc
valgrind --tool=callgrind named -g -c /etc/named.conf
```

Now query the resolver with a legitimate query:
```bash
dig test.home.lan
```
You should recieve a response with the IP address of test.home.lan (127.0.0.252)
```
;; QUESTION SECTION:
;test.home.lan.                 IN      A

;; ANSWER SECTION:
test.home.lan.          86400   IN      A  127.0.0.252
```
After receiving the response, stop the resolver.

Next we'll copy the results files from the docker container to the host.
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

In CloudLab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.

#### (E2) Throughput measurement experiment

If the malicious authoritative zone file `/env/nsd_attack/home.lan.forward` has not yet been configured with malicious domain names as described in E1, run
```bash
cp /env/reproduction/home.lan.forward /env/nsd_attack
```

This experiment requires a list of benign user domain names and attacker user domain names for the Resperf tool. Run
```bash
python /env/reproduction/genNamesToCheck.py
```
to generate two output files: "benignNamesE2.txt" and "attackerNamesE2.txt".

Make sure the resolver is configured to use Bind 9.16.6. To check the version run
```bash
named -v
```
If the resolver is using a different version, run
```bash
cd /env/bind9_16_6
make install
```
to change the version to Bind 9.16.6. Then run
```bash
cd /etc
named -g -c /etc/named.conf
```
to turn on the resolver.

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

You will run two "sub"-experiments. The first experiment will measure the effect of the attack on benign users throughput. The second experiment will measure the resolver throughput without any attack.

Benign and malicious users commands will be executed from two terminals inside the docker container each with an instance of the Resperf tool. The first will simulate the attacker and issue queries at a fixed rate, while the second tool will ramp up the benign user request until things start to fail. Open two terminals inside the docker, one for the malicious user and one for the benign user.

In the following tests, the malicious user command should be run first but ultimately in parallel to the benign user command.

From the malicious user run
```bash
resperf -d attackerNamesE2.txt -s 127.0.0.1 -v -m 15000 -c 60 -r 0 -R -P <output_file>
```
where -m is the number of QPS (15000) that are sent, -c is the duration of time (60) in which Resperf tries to send the queries, -r is the duration of time (0) in which Resperf ramps-up before sending the packets in constant time, and `<output_file>` is the output file name of your choice.

From the benign user run
```bash
resperf -d benignNamesE2.txt -s 127.0.0.1 -v -R -P <output_file>
```
substituting `<output_file>` with a unique file name of your choice.

Next, to measure the resolver throughput without any attack, "benignNamesE2.txt" will be used as the input files for both commands.

From the malicious user run
```bash
resperf -d benignNamesE2.txt -s 127.0.0.1 -v -m 15000 -c 60 -r 0 -R -P <output_file>
```
and from the benign user run
```bash
resperf -d benignNamesE2.txt -s 127.0.0.1 -v -R -P <output_file>
```
substituting `<output_file>` with a unique file name of your choice.

To view the results, open only the benign user output files from both sub-experiments. Compare the benign user throughput, the "responses_per_sec" column, between the two tests. You should observe a degradation in the resolver throughput for benign users during the NRDelegationAttack.

#### (E3) Instructions measurement experiment - NXNSAttack unpatched server

This experiment follows the instructions from the E1 experiment, but uses a Bind 9.16.2 resolver, which is not patched to NXNSAttack, instead of a Bind 9.16.6 resolver.

To change the Bind version run
```bash
cd /env/bind9_16_2
make install
```
to configure the resolver to use Bind 9.16.2

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

From another terminal in the docker environment, query the resolver with a malicious query:
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

In CloudLab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have more than 200,000,000.

#### (E4) Instructions measurement experiment - NRDelegation mitigation

This experiment follows the instructions from the E1 experiment, but uses a Bind 9.16.33 resolver, which is non-vulnerable to both NXNSAttack and NRDelegation attack, instead of a Bind 9.16.6 resolver.

To change the Bind version run
```bash
cd /env/bind9_16_33
make install
```
to configure the resolver to use Bind 9.16.2

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

From another terminal in the docker environment, query the resolver with a malicious query:
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

In CloudLab, open the VNC window and run
```bash
sudo kcachegrind ./callgrind.out.<VALGRIND_TEST_NUMBER>
```
to open the result file with the KCachegrind tool. In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function. Repeat this step with the second result file and compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have less than 10,000,000.

<!-- Analyze results -->

### Using VMs

<!-- Get resources -->
<!-- Configure resources -->
<!-- Run experiment -->
<!-- Analyze results -->

## Notes

### References

[1] Yehuda Afek, Anat Bremler-Barr, and Shani Stajnrod. 2023. NRDelegationAttack: Complexity DDoS attack on DNS Recursive Resolvers. In 32nd USENIX Security Symposium (USENIX Security 23), USENIX Association, Anaheim, CA, 3187–3204. Retrieved from https://www.usenix.org/conference/usenixsecurity23/presentation/afek
