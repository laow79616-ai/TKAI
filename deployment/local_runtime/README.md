# TKAI local deployment assets

Native Windows operation is the primary supported workflow. The repository-root
`docker-compose.local.yml` is an additional single-machine profile and does not
replace the PowerShell scripts.

Runtime state is bounded to `runtime/`. Configuration is initialized from
`configuration/local.example.json`; secrets remain external references.
