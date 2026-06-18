<!-- .slide: class="divider" -->
# Neo4j
## Technical Advisory

Operating a graph database in production

<span class="small">Banking fraud graph · Customer → Card → Purchase → Merchant · Account ⇄ Transfer</span>

Note:
Framing: we already have a working graph model (the fraud demo). This deck covers what it takes to run it in production and how it compares to the RDBMS world the audience knows.

===

## Agenda

1. **Infrastructure** — sizing, availability & consistency, DR, backup
2. **Data management** — migration, ingestion, ETL/ELT & pipelines
3. **Administration & tuning**
4. **Development process** — evolution, refactoring, Cypher
5. **Licensing**
6. **Competitive landscape**
7. **Use cases**

<span class="footer">Neo4j Technical Advisory</span>

===

<!-- .slide: class="divider" -->
## Infrastructure

===

## Sizing — the two memory pools

Neo4j stores the graph **on disk** and serves it through two tunable pools:

| Pool | What it holds | Rule of thumb |
|---|---|---|
| **Page cache** | hot graph + index pages | ≈ size of the store you want resident |
| **Heap (JVM)** | query execution, tx state | 8–31 GB (stay under compressed-oops 32 GB) |

```bash
# Ask Neo4j to recommend settings for a target machine
neo4j-admin server memory-recommendation --memory=32g
```

- **Index-free adjacency**: a hop is a pointer dereference, not an index lookup — traversal cost is independent of total graph size.
- Goal: keep the working set in page cache so traversals stay in RAM.

Note:
Index-free adjacency is the core performance story: relationship traversal is O(1) per hop regardless of how big the graph gets, unlike a relational JOIN which scales with table size. The classic benchmark: a deep friends-of-friends query stays flat as the graph grows while SQL JOINs blow up.

--

## Sizing — storage & capacity

- **Store size** ≈ records × fixed record sizes (nodes, relationships, properties) + indexes. Estimate from your CSV volumes.
- Neo4j 5 uses a new **block format** that removed the legacy 34B-entity ceiling — practical limits are now in the **quadrillions** of nodes/relationships.
- Capacity planning inputs:
  - ingest rate (transfers/purchases per day)
  - traversal depth & fan-out of hot queries (e.g. fraud ring detection)
  - concurrency (sessions × heap per query)
- **Scale-up first** (graph traversals love a single fast machine + big page cache); scale-out is for **read** throughput and HA, not sharding a connected graph.

<span class="note">Connected data resists naive sharding — a traversal that crosses shards pays network cost on every hop. Prefer one well-sized primary + read replicas. Use **Fabric** for federated/sharded topologies only when the domain genuinely partitions.</span>

===

## Availability & consistency

```
        ┌───────────┐   Raft   ┌───────────┐
writes →│ Primary 1 │◀────────▶│ Primary 2 │
        └─────┬─────┘ consensus└─────┬─────┘
              │        ┌───────────┐ │
              └───────▶│ Primary 3 │◀┘
                       └─────┬─────┘
              async │        │ async
            ┌───────▼──┐  ┌──▼───────┐
   reads →  │Secondary │  │Secondary │  (read scale-out)
            └──────────┘  └──────────┘
```

- **Autonomous Clustering** <span class="pill ee">Enterprise</span>: **Primaries** commit via **Raft** (majority quorum → strong consistency); **Secondaries** stream async for read scale-out.
- **Causal consistency** via **bookmarks**: read-your-own-writes across the cluster without forcing every read to the leader.
- Community Edition = **single instance** only (no clustering).

Note:
Raft gives you a strongly-consistent write path: a transaction is acknowledged once a majority of primaries have it. 3 primaries tolerate 1 failure, 5 tolerate 2. Bookmarks are the developer-facing consistency knob — the driver passes a bookmark so a follow-up read waits until the secondary has caught up to that transaction.

--

## Consistency model in practice

- **Writes**: ACID, fully serializable at commit, quorum-replicated.
- **Reads on secondaries**: eventually consistent unless you pass a **bookmark**.
- The driver chains bookmarks automatically within a session — cross-service flows pass bookmarks explicitly.

```python
# Causal chaining: the second tx sees the first, even on a different server
with driver.session() as s:
    s.execute_write(create_transfer)          # commits, returns a bookmark
    s.execute_read(detect_fraud_ring)         # guaranteed to see the transfer
```

<span class="note">For our fraud model: write the <code>Transfer</code> on a primary, then fan ring-detection reads out to secondaries — bookmarks ensure the new edge is visible.</span>

===

## Disaster recovery

- **Cluster across availability zones** within a region for HA; majority of primaries must survive to keep accepting writes.
- **Cross-region DR**: async **secondaries** in a second region → promote on regional failure (RPO ≈ replication lag, low-minutes RTO).
- **Backup-based DR**: restore latest backup + replay — higher RPO/RTO, lowest cost.
- Define and test targets explicitly:

| Strategy | RPO | RTO | Cost |
|---|---|---|---|
| Multi-AZ cluster | ~0 | seconds | $$ |
| Cross-region secondary | minutes | minutes | $$$ |
| Restore from backup | hours | hours | $ |

<span class="note">DR is only real if the **runbook is rehearsed** — schedule game-days that promote a secondary and restore a backup.</span>

===

## Backup

<div class="cols">

```bash
# Online, non-blocking backup — Enterprise only
neo4j-admin database backup neo4j \
  --to-path=/backups \
  --type=full      # or: differential

# Restore (aggregate full + diffs, then restore)
neo4j-admin database restore \
  --from-path=/backups/neo4j \
  --database=neo4j
```

- <span class="pill ee">Enterprise</span> **hot backup**: online, full + **differential** chains, no downtime.
- <span class="pill ce">Community</span> only `neo4j-admin database dump` — **offline** (stop the DB or dump a standby).
- <span class="pill aura">Aura</span> automated daily snapshots + on-demand, point-in-time within retention.

</div>

- Verify restores routinely; ship backups off-box (object storage) and **encrypt at rest**.
- **CDC** <span class="pill ee">Enterprise 5.x</span> complements backup for continuous downstream capture (not a backup substitute).

Note:
Key gotcha for prospects: Community Edition has no online backup and no clustering — those two facts usually drive the Enterprise/Aura decision more than anything else.

===

<!-- .slide: class="divider" -->
## Data Management

===

## Migration patterns (RDBMS → graph)

The mapping is mechanical once you internalise it:

| Relational | Graph |
|---|---|
| Row in a table | **Node** with a label |
| Primary key | Node property + **uniqueness constraint** |
| Foreign key | **Relationship** |
| Join table (M:N) | **Relationship** (often with properties) |
| Column you JOIN on a lot | Relationship / dedicated node |

- Don't lift-and-shift the schema — **model for the questions** (traversals), not for normalization.
- Our demo: a `purchases` join of card↔merchant becomes `(:Card)-[:FUNDS]->(:Purchase)-[:PAID_TO]->(:Merchant)`.

Note:
The single biggest migration mistake is recreating the relational schema 1:1 (e.g. a node per join table with two relationships when a single relationship would do). Model the traversals you actually run.

--

## Migration tooling

- **Neo4j Data Importer** — visual CSV → model mapping, generates the load.
- **`neo4j-admin database import`** — bulk, **offline**, fastest path for the initial load of large datasets.
- **APOC** — `apoc.load.jdbc` to pull straight from the source RDBMS; `apoc.periodic.iterate` for batched transforms.
- **Spark / Kafka connectors** — for large or streaming migrations.

```cypher
// Pull directly from the legacy system via JDBC (APOC)
CALL apoc.load.jdbc(
  'jdbc:postgresql://core-bank/accounts', 'SELECT * FROM customers'
) YIELD row
MERGE (c:Customer {cif: row.cif})
SET c.firstName = row.first_name, c.country = row.country;
```

===

## Ingestion — pick by volume & latency

| Method | Use when | Notes |
|---|---|---|
| `neo4j-admin database import` | initial bulk, **millions+** | offline, fastest, empty DB |
| `LOAD CSV` + `CALL { } IN TRANSACTIONS` | ongoing/medium loads | transactional, online |
| Driver + `UNWIND` batches | app-driven writes | parameterised, batch 1k–10k rows |
| **Kafka** Connect (sink) | streaming events | near-real-time |
| **Spark** connector | big distributed ETL | parallel writes |

```cypher
// Idempotent, batched online load (this repo's pattern)
LOAD CSV WITH HEADERS FROM 'file:///purchases.csv' AS row
CALL (row) {
  MATCH (card:Card {cardNumber: row.CardNumber})
  MATCH (m:Merchant {name: row.Merchant})
  CREATE (p:Purchase {transactionId: row.TransactionID, amount: toFloat(row.Amount)})
  CREATE (card)-[:FUNDS]->(p)-[:PAID_TO]->(m)
} IN TRANSACTIONS OF 1000 ROWS;
```

Note:
Always create constraints/indexes BEFORE a MERGE-heavy load, otherwise every MERGE does a full label scan and the load slows to a crawl. The repo creates uniqueness constraints on cif/cardNumber/accountNumber/merchant name first — that's exactly right.

--

## ETL / ELT & pipelines

- **ELT into the graph**: land raw, then transform with Cypher/APOC inside Neo4j — keeps the graph the single source of derived relationships.
- **Orchestration**: Airflow / Dagster trigger `neo4j-admin import`, `LOAD CSV`, or driver jobs on a schedule.
- **Streaming**: Kafka → Neo4j sink for events; **CDC** <span class="pill ee">5.x</span> emits Neo4j changes back out to downstream systems.
- **Spark** connector for distributed read/write against lakehouse data.

```
 Sources         Ingest            Graph              Downstream
 ───────         ──────            ─────              ──────────
 Core banking ─▶ Kafka/Spark  ─▶  Neo4j (model)  ─▶  CDC ─▶ feature store
 CSV / files  ─▶ LOAD CSV     ─▶  GDS algorithms ─▶  BI / fraud alerts
```

===

<!-- .slide: class="divider" -->
## Administration & Tuning

===

## Administration & tuning

<div class="cols">

**Schema & indexes**
- Uniqueness / node-key **constraints** (back-stopped by indexes)
- RANGE, TEXT, POINT, **FULL-TEXT**, and **vector** indexes
- Constraints enforce data quality *and* speed `MATCH`

**Query tuning**
- `EXPLAIN` (plan) / `PROFILE` (real db-hits)
- Anchor on an indexed node; cut cardinality early
- Parameterise → plan cache reuse

</div>

```cypher
PROFILE
MATCH (c:Customer {cif:'5'})-[:HAS_CARD]->(:Card)
      -[:FUNDS]->(p:Purchase)-[:PAID_TO]->(m:Merchant)
RETURN m.name, sum(p.amount) ORDER BY sum(p.amount) DESC;
```

- **Observability**: metrics (Prometheus/Graphite), `query.log` for slow queries, Ops Manager <span class="pill ee">EE</span>.
- **Tuning loop**: page-cache hit ratio → heap/GC → slowest queries by db-hits.

Note:
PROFILE shows db-hits per operator — the number to minimise. Watch for "AllNodesScan" or a big "NodeByLabelScan" with no index; that's the usual smell. Plan cache reuse only happens with parameterised queries, never string-concatenated ones.

===

<!-- .slide: class="divider" -->
## Development Process

===

## More amenable to evolution than RDBMS

- **Schema-optional**: labels and relationship types are additive — introduce `(:Merchant)-[:IN_CATEGORY]->(:Category)` without touching existing data or downtime.
- No `ALTER TABLE` locks, no nullable-column sprawl, no migration to backfill a new join table.
- **Refactor in place** with Cypher / APOC:

```cypher
// Promote a string property into a first-class node + relationship
MATCH (p:Purchase) WHERE p.merchantCategory IS NOT NULL
MERGE (cat:Category {name: p.merchantCategory})
MERGE (p)-[:IN_CATEGORY]->(cat)
REMOVE p.merchantCategory;
```

- Constraints are opt-in where you want guarantees — strong **where it matters**, flexible elsewhere.

Note:
The pitch vs RDBMS: in a relational world adding a many-to-many relationship means a new table, FKs, a migration, and app changes. In Neo4j it's a new relationship type that coexists with everything already there. Evolution is additive, not destructive.

--

## Cypher is intuitive

ASCII-art patterns read like the question you're asking:

```cypher
// "Which merchants did customer 5's cards pay?"
MATCH (c:Customer {cif:'5'})-[:HAS_CARD]->(:Card)
      -[:FUNDS]->(:Purchase)-[:PAID_TO]->(m:Merchant)
RETURN DISTINCT m.name;
```

<div class="cols">

**Cypher**
- Declarative; you describe the *pattern*
- `(node)-[:REL]->(node)` mirrors the whiteboard
- Open standard: **GQL** (ISO/IEC 39075, 2024) — Cypher is its foundation

**vs SQL for the same hop**
- 4 self-JOINs across customer, card, purchase, merchant
- intent buried in JOIN/ON boilerplate
- depth changes ⇒ rewrite the JOINs

</div>

Note:
GQL becoming an ISO standard in 2024 is a big de-risking point for skeptical buyers — graph query language is now a standard like SQL, and Cypher is the reference implementation. The "variable-depth" win is huge: `-[:REL*1..5]->` is one clause; the SQL equivalent is a recursive CTE.

===

<!-- .slide: class="divider" -->
## Licensing

===

## Licensing

| | <span class="pill ce">Community</span> | <span class="pill ee">Enterprise</span> | <span class="pill aura">Aura</span> |
|---|---|---|---|
| License | **GPLv3**, free | Commercial (subscription) | Managed SaaS (consumption) |
| Clustering / HA | ✗ single instance | ✓ Autonomous Clustering | ✓ managed |
| Online + differential backup | ✗ (offline dump only) | ✓ | ✓ automated |
| RBAC / fine-grained security | basic | ✓ roles, sub-graph, properties | ✓ |
| Multi-database, Fabric, CDC | ✗ | ✓ | ✓ (varies by tier) |
| Hot config, Ops Manager | ✗ | ✓ | n/a (managed) |

- **GDS** (Graph Data Science) is licensed separately — free tier + Enterprise.
- **Aura** tiers: Free → Professional → Business Critical → Virtual Dedicated Cloud.

<span class="note">Decision driver: need clustering, online backup, or RBAC → Enterprise or Aura. Single-node internal tool with offline backups → Community is genuinely free (GPLv3 obligations apply if you redistribute).</span>

===

<!-- .slide: class="divider" -->
## Competitive Landscape

===

## Where Neo4j sits

- **DB-Engines ranking**: **#1 graph DBMS** (by a wide margin), ~**#20 overall** across all database types.
- The reference implementation behind **GQL** (ISO standard) and **openCypher**.
- Mature operational story (clustering, backup, security) vs younger graph engines.

<div class="cols">

**Native graph competitors**
- TigerGraph, Memgraph, ArangoDB
- Amazon Neptune (LPG **and** RDF)
- Azure Cosmos DB (Gremlin API)

**Adjacent / embedded**
- **Apache AGE** (Postgres extension)
- JanusGraph (on Cassandra/HBase)
- RDF triple-stores (GraphDB, Stardog)

</div>

Note:
The #1-graph-but-#20-overall framing matters: graph is still a specialised segment. The competitive pressure increasingly comes from "graph as a feature" inside incumbents (Postgres+AGE, Cosmos) rather than pure-play graph vendors.

--

## LPG vs RDF — two graph philosophies

<div class="cols">

**Labeled Property Graph** (Neo4j)
- Nodes & relationships carry **properties** (key/value)
- Relationships are first-class & can hold data (e.g. `amount` on a transfer)
- Query: **Cypher / GQL**
- Optimised for **traversal & analytics**

**RDF / Triple-store**
- Everything is a `(subject, predicate, object)` triple
- **Global URIs**, formal ontologies (RDFS/OWL), reasoning
- Query: **SPARQL**
- Optimised for **interchange, inference, linked data**

</div>

- LPG: pragmatic, developer-friendly, great for fraud/recommendations/operational graphs.
- RDF: standards-driven semantics — data sharing across organisations, knowledge representation.
- Neo4j **`n10s` (neosemantics)** imports/exports RDF when you need both worlds.

Note:
Quick discriminator: can a relationship have a property? In LPG yes (the transfer amount sits on the edge). In RDF you'd need reification or a named-graph workaround. That edge-property ergonomics is why operational use cases gravitate to LPG.

--

## Apache AGE — the Postgres angle

- **A**pache **G**raph **E**xtension: adds graph + **openCypher** to PostgreSQL; query graph and relational **in one SQL statement**.
- Appeals to teams who want "just enough graph" without a new system to operate.

**Trade-offs vs Neo4j**

| | Apache AGE | Neo4j |
|---|---|---|
| Storage | on Postgres heap/indexes | **native** index-free adjacency |
| Deep-traversal perf | JOIN-like, degrades with depth | flat per-hop cost |
| Ecosystem | Postgres tooling | GDS, drivers, Bloom, Aura |
| Ops maturity for graph | early | production-proven clustering/backup |

<span class="note">Positioning: AGE is great for light graph workloads alongside existing Postgres. For deep traversals, graph algorithms (our fraud-ring / community detection), and graph-scale ops, native Neo4j keeps per-hop cost flat.</span>

===

<!-- .slide: class="divider" -->
## Use Cases

===

## Use cases

<div class="cols">

- **Fraud detection & AML** — ring detection, shared-device/account links *(this repo)*
- **Recommendations** — collaborative filtering over purchase graphs
- **Knowledge graphs / GraphRAG** — ground LLMs on connected facts + vector index
- **Network & IT ops** — dependency & impact analysis

- **Identity & access** — entitlement and reachability
- **Master data management** — entity resolution, golden records
- **Supply chain** — multi-tier traceability & risk
- **Customer 360** — unify across silos

</div>

```cypher
// Fraud ring: accounts reachable through transfers (variable depth)
MATCH path = (a:Account)-[:SENT_TO|RECEIVED_BY*2..6]-(b:Account)
WHERE a.flagged AND a <> b
RETURN b.accountNumber, length(path) ORDER BY length(path);
```

Note:
Tie it home: our banking model is the fraud-detection use case, and GDS (community detection, centrality) turns the same graph into features for an ML scoring pipeline. The variable-depth pattern is the thing relational simply can't express cleanly.

===

<!-- .slide: class="divider" -->
## Summary

- **Infra**: size two memory pools; cluster for HA; Enterprise/Aura for online backup & DR.
- **Data**: model for traversals; bulk-import then stream; constraints before load.
- **Dev**: additive schema evolution + intuitive Cypher/GQL beats RDBMS migrations.
- **Licensing**: clustering/backup/RBAC ⇒ Enterprise or Aura.
- **Landscape**: #1 graph DB; LPG ergonomics vs RDF semantics; AGE for light Postgres graph.

### Thank you — questions?

<span class="small">Press <strong>S</strong> for speaker notes · <strong>Esc</strong> for slide overview · <strong>F</strong> for fullscreen</span>
