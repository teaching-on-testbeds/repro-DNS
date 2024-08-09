## Background
<!-- this has background about the material. explain at a level suitable for an advanced undergrad with some background in the topic. -->

Distributed-denial-of-service (DDoS) attacks are attacks in which a malicious actor issues requests that consume a large amount of resources, resulting in performance degradation and eventually denial of service. Especially problematic are attacks when the effect of the initial bad request is amplified and an attacker, using only few resources, achieves a significant effect on the victim.

The Domain Name System (DNS) translates canonical names like "google.com" into the IP addresses that applications need to connect to the desired resource. During a DNS resolution without malicious activity, DNS resolvers, servers between the clients and the nameservers in the resolution process, respond to client requests by returning a cached name-to-address mapping or by forwarding the query to the DNS hierarchy until a resolution is reached. When a resolver's resources are exhausted with an attacker's requests, it is unable to complete the resolution process for legitimate clients. This kind of attack may be used to prevent users from accessing websites and web applications.

The NRDelegationAttack reproduced in this experiment exploits mechanisms that were introduced to mitigate a previous denial of service attack, the NXNSAttack, to amplify the effect of the malicious NRDelegation requests. The NXNSAttack[2], uses a malicious referral response with a list of non-existent nameservers. Upon receiving the malicious response, the resolver attempts to simultaneously resolve all names in the list.

![NXNSAttack_flow](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NXNSAttack_flow.svg)

To mitigate the effects of this attack, a referral limit and a “DNS_ADBFIND_NOFETCH” flag were implemented.

![NXNSAttack_mitigations_flow](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NXNSAttack_mitigations_flow.svg)

The resolver starts only resolving k, the referral limit, names and if all k attempts fail the resolution is aborted. The referral limit k = 5 for the BIND9 resolver used in this experiment, but varies for different resolver implementations. When a resolver reaches the limit the "DNS_ADBFIND_NOFETCH" ("No Fetch") flag is set. These mechanisms play a key role in the success of the NRDelegationAttack.

In the NRDelegationAttack [1], the attacker controls a malicious client and at least one malicious authoritative server. The malicious authoritative server is configured with a large malicious referral response, n = 1500 nameserver names, that delegates the resolution to a server non-responsive to DNS requests. The attack begins with the malicious client querying for a name that relies on the referral response.

![NRDelegationAttack_flow1](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/NRDelegationAttack_flow1.svg)

To process the referral response, the resolver looks up each of the n names in its cache and local memory for an existing resolution, totaling 2n lookups. Next, if k > n, the resolver turns on the "No Fetch" flag and starts resolving k of the n names. Each such name leads the resolver to a server that responds with the IP address of a server that is nonresponsive to DNS queries. Upon receiving this response a restart event is triggerd. The "No Fetch" flag is cleared because preserving it could prevent a valid name resolution, and in parallel, the resolver 1. restarts resolving the referral response for the next k names, while 2. querying the received IP address and fails to get a response. The attack will loop through the names in referral response, repeating the 2n lookups.

![NRDelegationAttack_resolution](https://github.com/grcmcdvtt/repro-DNS/raw/main/images/mal_resolution.svg)

The attack continues, the resolver attempting to process the referral response in blocks of k names, until either a restart limit is reached or a timeout occurs. The main source of the attack's resource consumption is the repetition of the 2n lookups.
