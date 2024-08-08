#### Instructions measurement experiment - NXNS-unpatched resolver

This experiment follows the instructions from the NXNS-patched experiment, but uses a BIND9.16.2 resolver, which is an NXNS-unpatched resolver, instead of a BIND9.16.6 resolver. 

To change the BIND9 version, run
```bash
cd bind9_16_2
sudo make install
```
to configure the resolver to use BIND9.16.2.

Turn on the resolver with Valgrind's callgrind tool by running
```bash
sudo valgrind --tool=callgrind --callgrind-out-file=mal_nxns_unpatched named -g
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
sudo valgrind --tool=callgrind --callgrind-out-file=benign_nxns_unpatched named -g
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
