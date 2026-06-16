[working-directory: '/opt/homebrew/var/neo4j/data'] 
reset:
  neo4j stop
  rm -rf databases/neo4j
  rm -rf transactions/neo4j
  neo4j start
