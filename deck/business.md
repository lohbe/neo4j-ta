<!-- .slide: class="divider" -->
# Neo4j
## Business &amp; Strategy

Why a graph database — and when it changes the game

<span class="small">A practical lens, grounded in the banking fraud demo</span>

Note:
This is the executive / decision-maker narrative. Goal: leave the room able to answer "what is it, why is it different, when does it pay off, and how do we start." We end on business value, not technology.

===

## Agenda

1. **Intro** — what Neo4j is
2. **How is it different?** — vs RDBMS
3. **How is it better?** — filling a critical business gap
4. **When is it better?** — the conditions that pay off
5. **How do we get onboard?** — a pragmatic on-ramp
6. **Demo** — fraud, from questions to answers
7. **Conclusion** — value &amp; impact

===

<!-- .slide: class="divider" -->
## Intro to Neo4j

===

## What is Neo4j?

- The world's **most widely adopted graph database** — data stored as **nodes** and the **relationships** between them, not rows in tables.
- Relationships are **first-class citizens**: stored, named, directed, and able to carry their own data.
- You query the *connections* directly with **Cypher** — a visual, pattern-based language.

<div class="cols">

**The shape of the data**
```
(Customer)-[:HAS_CARD]->(Card)
   -[:FUNDS]->(Purchase)
   -[:PAID_TO]->(Merchant)
```

**Why it matters to the business**
- Questions about *how things connect* become **simple and fast**.
- The model looks like the **whiteboard** the business already draws.

</div>

Note:
Anchor on the whiteboard idea: when a domain expert sketches the business on a whiteboard, they draw circles and arrows — a graph. Neo4j stores exactly that, so there's no translation loss between how the business thinks and how the data is stored.

===

<!-- .slide: class="divider" -->
## How is it different?

===

## Different — vs the relational database

| | **Relational (RDBMS)** | **Graph (Neo4j)** |
|---|---|---|
| Core unit | Tables &amp; rows | Nodes &amp; relationships |
| Connections | Foreign keys, resolved at **query time** | Stored **directly**, traversed as pointers |
| "Who connects to whom?" | **JOINs** across tables | Follow the relationship |
| Cost of a deeper question | More JOINs, slower | **Flat** per hop |
| Schema change | Migrations, `ALTER TABLE` | **Additive**, no downtime |

- In an RDBMS, relationships are **inferred** every time you ask — by matching keys across tables.
- In a graph, relationships are **stored once** and simply **followed** — so connected questions stay fast as they get deeper.

Note:
The single sentence to land: relational databases store data well but treat relationships as an afterthought computed at query time; graph databases store the relationships themselves. Every JOIN is the database re-discovering a connection it could have just stored.

--

## The same question, two ways

<div class="cols">

**SQL — "merchants paid by customer 5's cards"**
```sql
SELECT DISTINCT m.name
FROM customer c
JOIN card cd   ON cd.cif = c.cif
JOIN purchase p ON p.card_number = cd.card_number
JOIN merchant m ON m.name = p.merchant
WHERE c.cif = '5';
```

**Cypher — same question**
```cypher
MATCH (c:Customer {cif:'5'})-[:HAS_CARD]->(:Card)
      -[:FUNDS]->(:Purchase)-[:PAID_TO]->(m:Merchant)
RETURN DISTINCT m.name;
```

</div>

<span class="note">Four JOINs vs one readable path. Now ask "anyone within 4 hops of a flagged account" — in SQL that's a recursive query few can write; in Cypher it's <code>-[:SENT_TO|RECEIVED_BY*1..4]-</code>.</span>

===

<!-- .slide: class="divider" -->
## How is it better?

===

## Better — it fills a critical business gap

> The value in your data increasingly lives in the **connections** — and that's exactly what tables make expensive to see.

- Real business questions are **relationship questions**: *fraud rings, recommendations, dependencies, supply chains, customer 360.*
- In a relational world those answers are **buried under join complexity** — slow to run and slow to build, so they often don't get asked at all.
- Graph makes connected questions **cheap to ask and natural to express**, so the business can finally act on them.

<div class="cols">

**What you gain**
- See patterns that span **many hops**
- Answers in **real time**, not overnight batch
- Models that **match the business**

**What it unlocks**
- Detect **fraud rings**, not just bad transactions
- Discover **hidden clusters &amp; cycles**
- Ship new questions **without re-architecting**

</div>

Note:
The gap framing is the heart of the strategy pitch: it's not that relational is "bad," it's that relationship-centric questions are precisely where it's weakest — and those questions are where competitive advantage increasingly sits. Graph turns "too hard to ask" into "answered in real time."

===

<!-- .slide: class="divider" -->
## When is it better?

===

## When — the conditions that pay off

Graph wins when the **connections are the point**. The more of these are true, the bigger the payoff:

1. **Primary data is highly networked** — entities reference many other entities (customers ↔ accounts ↔ transfers ↔ merchants).
2. **And networked deeply** — the questions span **many hops**, not just one join (rings, paths, reachability).
3. **Large transactional &amp; analytical volumes exacerbate the problem** — at scale, JOIN-heavy queries slow down; graph traversal cost stays **flat per hop**.
4. **It supplements the relationship-gap in columnar data** — warehouses/columnar stores aggregate beautifully but can't *traverse*; graph complements them where connections matter.

<span class="note">Rule of thumb: if your hardest questions start with "how is X connected to Y through…" — and the answer needs more than one or two joins — that's a graph problem.</span>

Note:
Walk these four as a qualifying checklist for the audience's own data. Point #4 is important for shops that just invested in a warehouse: this isn't rip-and-replace. Columnar/warehouse is great at "sum by dimension"; graph is great at "trace the path." They coexist — graph fills the relationship gap.

--

## Where it pays off — and where it doesn't

<div class="cols">

**Strong fit**
- Fraud &amp; AML — rings, mules, shared identities
- Recommendations &amp; personalization
- Knowledge graphs / GraphRAG for AI
- Network, IT &amp; supply-chain dependencies
- Identity, entitlements, customer 360

**Weaker fit (keep relational/columnar)**
- Simple CRUD on isolated records
- Heavy tabular aggregation / reporting
- Flat data with few relationships

</div>

<span class="note">Strategy isn't "replace the RDBMS" — it's "add graph where connections drive value," alongside the systems you already run.</span>

===

<!-- .slide: class="divider" -->
## How do we get onboard?

===

## On-ramp — start from the questions, not the schema

A pragmatic, low-risk path that reuses the data you already have:

1. **Start with the questions** you need to answer — or the places where **join-complexity** is hurting you today.
2. **Gather the important tables** that those questions touch (customers, cards, purchases, transfers…).
3. **Observe the columns** — keys become **relationships**, descriptive fields become **properties**.
4. **Design natively for the questions** — model the graph around how you'll *traverse* it, not around normalization.

```
 Questions  ─▶  Key tables  ─▶  Columns  ─▶  Native graph model
 (or pain)      (the data)      → nodes,        (fits the questions)
                                  rels, props
```

<span class="note">This is days-to-weeks, not a multi-quarter migration. Existing CSV/table exports load straight in — start with one high-value question and grow.</span>

Note:
De-risking message: you don't boil the ocean or migrate everything. Pick one painful, high-value question, pull the handful of tables behind it, map columns to a graph, load, and answer it. The win funds the next iteration. This is exactly the path the demo took.

===

<!-- .slide: class="divider" -->
## Demo — Fraud

===

## What the demo showed

The banking fraud model, built the same way we just described:

1. **Domain modeled from the questions** — customers, cards, accounts, purchases, transfers and merchants, loaded directly from existing CSV exports.
2. **Questions powered the Cypher** — almost intuitively; the query *looks like* the question being asked.
3. **Graph algorithms run in the database** — discover **cycles and clusters** that are effectively invisible in columnar/tabular form.

```cypher
// Community detection groups colluding accounts into rings
CALL gds.louvain.stream('xfers')
YIELD nodeId, communityId;
```

Note:
The demo is the proof of the on-ramp. Emphasise two payoffs: (1) speed-to-model — questions + existing data became a working graph quickly; (2) the algorithm angle — Louvain/centrality/cycle detection surface fraud *rings*, the multi-account structures that per-transaction relational rules never see. That's net-new business capability, not just a faster version of the old query.

--

## Why that's hard the old way

<div class="cols">

**Relational / columnar**
- Per-transaction rules: "amount &gt; X"
- Rings need **recursive self-joins** — slow, brittle, rarely built
- Clusters live across rows no single query connects
- Patterns surface **after the fact**, in batch

**Graph (Neo4j)**
- Traverse the **whole network** of money flow
- Cycles &amp; communities are **built-in algorithms**
- Rings surface as **structure**, in real time
- New fraud patterns = **new query**, not new pipeline

</div>

<span class="note">The fraudster's advantage is that they operate as a *network*. Graph lets you investigate them as one.</span>

===

<!-- .slide: class="divider" -->
## Conclusion

===

## Business value

- **Ask the questions that were too hard to ask** — connected, multi-hop questions become simple and fast.
- **Real-time answers** where relational needed overnight batch — fraud caught *as it happens*.
- **Faster delivery** — model matches the business, schema evolves additively, new questions ship without re-architecting.
- **Higher-value insight** — find **rings, cycles and clusters**, not just isolated records.
- **Protects existing investment** — complements your RDBMS and warehouse; adopt incrementally where connections drive value.

===

<!-- .slide: class="divider" -->
## Impact

- **Revenue &amp; loss avoidance** — detect fraud rings and risk earlier; better recommendations lift conversion.
- **Speed to insight** — questions answered in real time, projects delivered in weeks.
- **Agility** — evolve the model as the business changes.
- **Competitive edge** — act on the connections in your data before competitors can see them.

### The connections in your data are an asset. Neo4j lets you use them.

<span class="small">Press <strong>S</strong> for speaker notes · <strong>Esc</strong> for overview · <strong>F</strong> for fullscreen</span>
