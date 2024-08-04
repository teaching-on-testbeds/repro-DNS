## Results
<!-- Here, you'll show: the original result in the paper and output from your experiment reproducing it. -->

The following figure shows the instructions executed on the resolver CPU relative to the referral response size for both NXNS-patched and non-patched BIND9 resolvers from the original result in the paper:

![attack_cost_paper](https://github.com/user-attachments/assets/a35ebdb7-3654-4c49-b24b-e3ca627a02a4)

As the NXNS attack mitigations empower their NRDelegationAttack, Afek et al. [1] finds that a resolver patched against the NXNS attack is more vulnerable to the attack (costs more instructions) than a non-patched resolver implementation.

For a NXNS-patched resolver, Afek et al. [1] claims that if the referral list is large, e.g 1,500 NS names, then each NRDelegationAttack malicious query costs at least 5,600 times more CPU instructions than a benign query, reporting 3,415,000,000 instructions for a malicious query and around 195,000 for a benign query. 

Efforts to reproduce the instructions measurement experiments recorded 2,775,000,000 instructions for a malicious query and around 200,000 instructions for a benign query on a NXNS-patched resolver.

![attack_cost_repro](https://github.com/user-attachments/assets/993b98a2-7da7-4241-b651-2b1acfdf4e15)

(The cost(n) function was developed in Afek et al. [1]  and predicts the number of instructions executed during a NRDelegationAttack on BIND9. The function depends only on the number of referrals in the referral response)

This experiment will measure the instructions executed for malicious and benign queries on patched and unpatched BIND9 implementations&mdash;you should observe around 200,000 instructions for a benign query, more than 2,000,000,000 instructions for a malicious query on the NXNS-patched resolver, and around 200,000,000 on the NXNS-unpatched resolver. Additionally, we will test malicious and benign queries on a resolver patched against the NRDelegationAttack.

Afek et al. [1] proposed three different mitigation mechanisms. The following figure shows the original results in the paper for the reduction in the effect of the attack under the proposed mitigations:

![mitigations_cost_paper](https://github.com/user-attachments/assets/a1aaa63c-68e4-4b52-b189-1fa4a0edc3ee)

Following the responsible disclosure procedure by Afek et al. [1], CVE-2022-2795 [3] was issued and the Internet Systems Consortium patched BIND9 against the NRDelegationAttack, limiting the number of database lookups performed when processing delegations, in the 9.16.33 version [4]. The figure below encompasses the results we obtained when reproducing the NRDelegationAttack on NXNS-patched, NXNS-unpatched, and NRDelegation-patched resolver implementations.

![attack_cost_mitigation_repro](https://github.com/user-attachments/assets/a52e7eca-ce3d-43a2-8efa-aa6d48c85a73)

When analyzing the effectiveness of a DDoS attack, we are interested in the attack's impact on resolver throughput (the ratio between resolver responses per second and received queries per second). The experiment will test resolver throughput with and without the NRDelegationAttack.

![throughput_no_attack](https://github.com/user-attachments/assets/bede7339-17f8-459e-b21b-b105c0150faf)![throughput_attack](https://github.com/user-attachments/assets/14b58229-1fa5-406a-b8df-4da5f3dc43e6)

When the resolver is under attack, you should observe a significant performance degradation: the benign client receives 0 responses per second for its queries. Without a response, the client is unable to connect to the requested service.
