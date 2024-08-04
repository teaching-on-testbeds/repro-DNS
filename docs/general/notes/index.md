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
