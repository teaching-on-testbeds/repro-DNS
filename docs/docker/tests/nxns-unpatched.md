### Instructions measurement experiment - NXNS-unpatched resolver

This experiment follows the instructions from the NXNS-patched experiment, but uses a BIND9.16.2 resolver, which is an NXNS-unpatched resolver. 

To change the BIND9 version, run
```bash
cd /env/bind9_16_2
make install
```
to configure the resolver to use BIND9.16.2.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=mal_nxns_unpatched named -g -c /etc/named.conf
```

If the authoritative servers are not running, run 
```bash
cd /env/nsd_root
nsd -c nsd.conf -d -f nsd.db
```
to turn on the root and run
```bash
cd /env/nsd_attack
nsd -c nsd.conf -d -f nsd.db
```
to turn on the attack server. You can check if the `nsd` process is running with the `ps aux | grep nsd` command.

From Client 1, query the resolver with a malicious query:
```bash
dig attack0.home.lan.
```

Stop the resolver and restart it with the Valgrind tool:
```bash
cd /etc
valgrind --tool=callgrind --callgrind-out-file=benign_nxns_unpatched named -g -c /etc/named.conf
```

Now query the resolver with the legitimate query:
```bash
dig test.home.lan
```
After receiving a response (IP address 127.0.0.252), stop the resolver.

Next we'll copy the results files from the docker container to the host machine. From the host, run
```bash
sudo docker cp $CONTAINER_ID:/etc/mal_nxns_unpatched $(eval echo ~)/mal_nxns_unpatched
sudo docker cp $CONTAINER_ID:/etc/benign_nxns_unpatched $(eval echo ~)/benign_nxns_unpatched
```
After copying the files, run
```bash
sudo chown $USER $(eval echo ~)/mal_nxns_unpatched
sudo chown $USER $(eval echo ~)/benign_nxns_unpatched
```
to add permissions to open the files.

In Cloudlab, open the VNC window and run
```bash
sudo kcachegrind $(eval echo ~)/mal_nxns_unpatched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind $(eval echo ~)/benign_nxns_unpatched
```
to open the benign query results file.

In the KCachegrind GUI, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both files. Compare the results. The benign query results should be around 200,000 instructions, while the malicious query should have around 200,000,000.
