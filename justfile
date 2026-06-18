set default-list := true

# Serve the reveal.js decks with live reload on save
# Technical Advisory: http://localhost:4321/   Business & Strategy: http://localhost:4321/business.html
[working-directory: 'deck']
deck:
  npx --yes live-server --port=4321 --watch=slides.md,business.md,theme.css,index.html,business.html .

[working-directory: '/opt/homebrew/var/neo4j/data']
reset:
  neo4j stop
  rm -rf databases/neo4j
  rm -rf transactions/neo4j
  neo4j start

[working-directory: '/opt/homebrew/Cellar/neo4j/2026.05.0/libexec']
install-gds:
  curl -Lo /tmp/gds.zip 'https://graphdatascience.ninja/neo4j-graph-data-science-2026.05.0.zip'
  unzip /tmp/gds.zip -d ./plugins/
  echo remember in  neo4j.conf:
  echo dbms.security.procedures.unrestricted=gds.*
  echo dbms.security.procedures.allowlist=gds.*

# A comma separated list of procedures and user defined functions that are allowed
# full access to the database through unsupported/insecure internal APIs.
#dbms.security.procedures.unrestricted=my.extensions.example,my.procedures.*
#dbms.security.procedures.unrestricted=gds.*

# A comma separated list of procedures to be loaded by default.
# Leaving this unconfigured will load all procedures found.
#dbms.security.procedures.allowlist=apoc.coll.*,apoc.load.*,gds.*
#dbms.security.procedures.allowlist=gds.*
