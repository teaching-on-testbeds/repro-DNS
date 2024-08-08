#### Instructions measurement experiment - NXNS-patched resolver

This experiment will measure the CPU instructions executed on a NXNS-patched resolver (BIND9.16.6) during a malicious query compared to a benign query. The number of instructions will be recorded by an instance of the callgrind tool in the command to start the resolver.

Make sure the resolver is configured to use BIND9.16.6. Run `named -v` to check the version. If the resolver is using a different version, run:
```bash
cd bind9
sudo make install
```
to change the version to BIND9.16.6.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=mal_nxns_patched named -g
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
sudo valgrind --tool=callgrind --callgrind-out-file=benign_nxns_patched named -g
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
sudo kcachegrind mal_nxns_patched
```
to open the malicious query results file with the KCachegrind tool. And run
```bash
sudo kcachegrind benign_nxns_patched
```
to open the benign query results file.

In the KCachegrind interface, make sure the "Relative" button is unchecked and choose the "Instructions Fetch" tab. Record the "Incl." value of the `fctx_getaddresses` function for both results files. Compare the results. The benign query should be around 200,000 instructions, while the malicious query should have more than 2,000,000,000.
