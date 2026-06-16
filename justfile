create:
  cypher-shell -u neo4j -p password <<'EOF'
  // https://neo4j.com/docs/operations-manual/current/database-administration/standard-databases/create-databases/
  :use system;

  CREATE DATABASE bank IF NOT EXISTS;
  CREATE USER analyst IF NOT EXISTS;
  SET PASSWORD 'Password123!'
  CHANGE NOT REQUIRED;

  // https://neo4j.com/docs/operations-manual/current/authentication-authorization/manage-roles/#:~:text=architect,-%2D%20can
  GRANT ROLE architect TO analyst;
  GRANT ACCESS ON DATABASE bank TO analyst;
  REVOKE ACCESS ON DATABASE neo4j FROM analyst;
  EOF

delete:
  cypher-shell -u neo4j -p password <<'EOF'
  // https://neo4j.com/docs/operations-manual/current/database-administration/standard-databases/delete-databases/
  :use system;

  REVOKE ROLE architect FROM analyst;
  REVOKE ACCESS ON DATABASE customer FROM analyst;

  DROP USER analyst IF EXISTS;

  STOP DATABASE bank IF EXISTS;
  DROP DATABASE bank IF EXISTS;
  EOF

