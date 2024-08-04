#### Instructions measurement experiment - NXNS-patched resolver

This experiment will measure the CPU instructions executed on a NXNS-patched resolver (BIND9.16.6) during a malicious query compared to a benign query. The number of instructions will be recorded by an instance of the callgrind tool in the command to start the resolver.

Make sure the resolver is configured to use BIND9.16.6. Run `named -v` to check the version. If the resolver is using a different version, run:
```bash
cd /env/bind9_16_6
make install
```
to change the version to BIND9.16.6.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nxns_patched named -g -c /etc/named.conf
```
We use `--tool=callgrind` to specify that we are using the callgrind tool. `named` is the BIND9 service and `/etc/named.conf` is the configuration file.

The malicious referral response should include a long list of name servers, in order to create such a response, the `/env/nsd_attack/home.lan.forward` zone file needs to have 1500 records per one malicious request. From the Malicious server, run
```bash
cp /env/reproduction/home.lan.forward /env/nsd_attack
```
to load the zone file for the malicious authoritative server. Then run 
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server.

In the Root server terminal, run
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root server

From Client 1, query the resolver with a malicious query:
```bash
dig attack0.home.lan.
```
The malicious referral response contains 1500 records that delegate the resolution of `attack0.home.lan` to a DNS non-responsive server. You will not receive a resolution for the name `attack.home.lan` because the resolver was directed to resolve the name at a server incapable of responding to the DNS queries. Instead, you will see a message with `status: SERVFAIL`:
```
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: SERVFAIL, id: 26296
;; flags: qr rd ra; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1
```

Stop the resolver (Ctrl+C) and restart it with the Valgrind tool:
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nxns_patched named -g -c /etc/named.conf
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

Next we'll copy the results files from the docker container to the host machine. From the host, run
```bash
sudo docker cp $CONTAINER_ID:/etc/mal_nxns_patched $(eval echo ~)/mal_nxns_patched
sudo docker cp $CONTAINER_ID:/etc/benign_nxns_patched $(eval echo ~)/benign_nxns_patched
done
```
After copying the files, run
```bash
sudo chown $USER $(eval echo ~)/mal_nxns_patched
sudo chown $USER $(eval echo ~)/benign_nxns_patched
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind $(eval echo ~)/mal_nxns_patched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind $(eval echo ~)/benign_nxns_patched
```
to open the bening query results file.

In the tool, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both results files. Compare the results. The benign query should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.
