We will refer to the cost of a NRDelegation query as the number of resolver CPU instructions executed during a malicious query. The NRDelegation attack is harmful because a single query costs significantly more than a benign query. This experiment will measure the cost of malicious and benign queries on a NXNS-patched resolver (BIND9.16.6), a NXNS-unpatched resolver (BIND9.16.2), and a NRDelegation-patched resolver (9.16.33).

- [Test NRDelegationAttack on a NXNS-patched resolver](nxns-patched.md)
- [Test NRDelegationAttack on a NXNS-unpatched resolver](nxns-unpatched.md)
- [Test NRDelegationAttack on a NRDelegation-patched resolver](nrdelegation-patched.md)
- [Test NRDelegationAttack with different referral list lengths](other-tests.md)
