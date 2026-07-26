# Signing and Integrity

Package releases carry separate checksum and signature fields. Production
adapters must verify the artifact digest and publisher signature before
publication or installation, bind signing keys to verified publisher profiles,
rotate keys, and preserve an audit record. The reference domain stores these
values but never reads artifacts or secrets.
