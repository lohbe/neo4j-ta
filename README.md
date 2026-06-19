# Neo4j — Banking Fraud Demo

A solutions-engineering demo for Neo4j, built around a synthetic banking dataset.
It pairs a live, runnable [Marimo](https://marimo.io) notebook with a banking customer
[reveal.js](https://revealjs.com) slide deck.

## What's inside

| Path | What it is |
|------|------------|
| [`customer.py`](customer.py) | Marimo notebook — the live demo: graph modeling, ingestion, Cypher fraud queries, merchant analytics, and GDS community detection. |
| [`deck/`](deck/) | reveal.js deck for banking customer. See [`deck/README.md`](deck/README.md). |
| [`deck/preso.pdf`](deck/preso.pdf) | Pre-exported PDF of the deck, for quick viewing without a server. |
| [`customers.csv`](customers.csv), [`purchases.csv`](purchases.csv), [`transfers.csv`](transfers.csv) | The synthetic dataset loaded by the notebook. |
| [`justfile`](justfile) | Helper recipes (`just deck`, `just reset`, `just install-gds`). |

## The dataset

Synthetic banking [data](https://gist.github.com/sumitshatwara/19bf6eb6f6a5adecddedf2a081b51789) — no real customers. Customers hold cards and accounts;
purchases hit cards, transfers move money account-to-account.

| File | Rows | Key columns |
|------|------|-------------|
| `customers.csv` | 100 | `CIF`, `Age`, `Gender`, `Address`, `Country`, `JobTitle`, `CardNumber`, `AccountNumber` |
| `purchases.csv` | 10,000 | `TransactionID`, `CardNumber`, `Merchant`, `Amount`, `PurchaseDatetime`, `CardIssuer` |
| `transfers.csv` | 1,000 | `TransactionID`, `SenderAccountNumber`, `ReceiverAccountNumber`, `Amount`, `TransferDatetime` |

## What the demo covers

The notebook runs top-to-bottom as a guided story:

1. **Dataset overview** — load and inspect the three CSVs; surface duplicate transaction IDs.
2. **Graph data modeling & ingestion** — domain, core model, constraints, and a clean Cypher load of customers, cards, accounts, merchants, purchases, and transfers.
3. **Cypher query development** — a fraud study: zoom in on a suspect (`CIF = 5`), trace transaction history, and pivot through shared relationships.
4. **Merchant analytics** — occupation mix and age skew across each merchant's customer base.
5. **Graph Data Science** — project an account-to-account graph, run Weakly Connected Components and Louvain, read the modularity score, and cross-reference communities against shared `country` / `address` attributes.

## Prerequisites

- **Neo4j** installed locally and reachable on the default ports (`bolt://localhost:7687`), ideally with an empty default database. See [Neo4j install docs](https://neo4j.com/docs/operations-manual/current/installation/).
  > **Warning:** the notebook **drops all objects from the default database** on run. Point it at a throwaway instance.
- **[GDS (Graph Data Science) plugin](https://neo4j.com/docs/graph-data-science/current/installation/)** — required for the community-detection section. `just install-gds` automates this for a Homebrew install (adjust the version path inside the recipe to match yours).
- **Python ≥ 3.14** and **[uv](https://docs.astral.sh/uv/)** to run the notebook.
- *(optional)* **[just](https://github.com/casey/just)** — the command runner used for the recipes below.

## Quick start

Once Neo4j (with GDS) is running:

```bash
uvx marimo edit --sandbox customer.py
```

`uv` resolves the notebook's pinned dependencies (declared inline in
[`customer.py`](customer.py)) into an isolated sandbox — no manual `pip install`
needed. Step through the cells to run the demo.

> The notebook uses the default Neo4j connection. If your instance needs
> credentials or a non-default URI, update the `GraphDatabase.driver(...)` call
> in the connection cell.

## `just` recipes

| Recipe | What it does |
|--------|--------------|
| `just deck` | Serve both reveal.js decks with live reload (Technical Advisory at <http://localhost:4321/>, Business & Strategy at <http://localhost:4321/business.html>). |
| `just reset` | Stop Neo4j, wipe the default database files, restart — a clean slate between demo runs. *(Homebrew paths; adjust if your install differs.)* |
| `just install-gds` | Download and install the GDS plugin into a Homebrew Neo4j install, and print the `neo4j.conf` settings to enable it. |

> The `reset` and `install-gds` recipes hard-code Homebrew paths and a specific
> Neo4j version. Open [`justfile`](justfile) and adjust them to match your
> install before running.

## The slide decks

The deck lives under [`deck/`](deck/), one theme and a live-preview harness. For a quick read with no setup, open [`deck/preso.pdf`](deck/preso.pdf).

## Notes

- Built and tested against a Homebrew Neo4j install 2026.05.0 (the `justfile` reflects
  that). Other installs work — just update the paths in the recipes.
- The ingestion is written for **Community Edition** (no `CREATE DATABASE`); it
  works against the default database rather than creating a dedicated one.
