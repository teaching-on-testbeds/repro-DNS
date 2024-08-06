#### Instructions measurement experiment - NRDelegation-patched resolver

This experiment will measure the instructions executed on a resolver implementation (BIND9.16.33) patched against the NRDelegationAttack.

To change the BIND9 version, run
```bash
cd /env/bind9_16_33
make install
```
to configure the resolver to use BIND9.16.33.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nrdelegation_patched named -g -c /etc/named.conf
```

If the authoritative servers are not turned on, run 
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

From Client 1, query the resolver with a malicious query:
```bash
dig attack0.home.lan.
```

Once the malicious name resolution fails, stop the resolver and restart it with the Valgrind tool:
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nrdelegation_patched named -g -c /etc/named.conf
```

Now query the resolver with the legitimate query:
```bash
dig test.home.lan
```
After receiving a response (IP address 127.0.0.252), stop the resolver.

Next we'll copy the results files from the docker container to the host machine. From the host, run
```bash
sudo docker cp $CONTAINER_ID:/etc/mal_nrdelegation_patched $(eval echo ~)/mal_nrdelegation_patched
sudo docker cp $CONTAINER_ID:/etc/benign_nrdelegation_patched $(eval echo ~)/benign_nrdelegation_patched
```
After copying the files, run
```bash
sudo chown $USER $(eval echo ~)/mal_nrdelegation_patched
sudo chown $USER $(eval echo ~)/benign_nrdelegation_patched
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind $(eval echo ~)/mal_nrdelegation_patched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind $(eval echo ~)/benign_nrdelegation_patched
```
to open the benign query results file.

Make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both files. Compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have around 10,000,000.
