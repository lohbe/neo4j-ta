# /// script
# dependencies = [
#     "altair==6.2.1",
#     "marimo",
#     "neo4j==6.2.0",
#     "pandas==3.0.3",
#     "py==1.11.0",
#     "pyarrow==24.0.0",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium", auto_download=["html"])


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    from neo4j import GraphDatabase

    import altair as alt

    return GraphDatabase, alt, mo, pd


@app.cell
def _(mo):
    callout = mo.callout("DANGER: This script wipes the ENTIRE default neo4j database at localhost", kind="danger")
    mo.vstack([callout], align="stretch", gap=0)
    return


@app.cell
def _(mo):
    mo.outline(label="Table of Contents")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Dataset Overview
    """)
    return


@app.cell
def _(mo, pd):
    with mo.status.spinner("Loading data"):
        customers = pd.read_csv("customers.csv")
        purchases = pd.read_csv("purchases.csv")
        transfers = pd.read_csv("transfers.csv")
    return customers, purchases, transfers


@app.cell
def _(customers):
    customers['CIF'] = customers['CIF'].astype(str)
    customers
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This set of data appears to be a snapshot from an analytical database between Jan 1 2021 and Sep 7 2021. When importing the data, some columns were casted into proper types for more accurate analysis.

    `customers.csv` contains details about banking customers. There are 100 customers, each represented by a row. Each customer has one and only one CIF, one credit card and one account number. These are all unique, so classic fraud signals like mule networks would not appear in this dataset.

    `JobTitle` is not completely unique, and might be amenable for merchant analytics.
    """)
    return


@app.cell
def _(pd, purchases):
    purchases['TransactionID'] = purchases['TransactionID'].astype(str)
    purchases['PurchaseDatetime'] = pd.to_datetime(purchases['PurchaseDatetime'], format='ISO8601')
    purchases
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `purchases.csv` contains details of 10,000 transactions with a set of 30 merchants made through the customers' card. Transactions here imply flow of credit from customer to merchant - this can be represented as directed edges/relationships in neo4j.

    In traditional relational databases, to find out who made the purchase, this table with `CardNumber` needs to be joined with another `customer` table. This is an expensive operation, because these tables are extremely large. In graph databases however, JOINs are not necessary because purchases stored as graphs can be quickly matched and traversed.

    There are 42 duplicate `TranscationID`s - this is generally considered a **red flag** for potential replay attacks, exploits or account takeovers - or some unintentional system issue (glitches, double clicking, distributed system coordination, etc). This is worth checking out - so we need to preserve the duplicates while loading data into neo4j.
    """)
    return


@app.cell
def _(pd, transfers):
    transfers['TransactionID'] = transfers['TransactionID'].astype(str)
    transfers['TransferDatetime'] = pd.to_datetime(transfers['TransferDatetime'], format='ISO8601')
    transfers
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `transfers` contains details of 1,000 credit transfers between customer accounts. This can be represented as a sending-to or receive-from relationship/edge in neo4j.

    There is one non-unique `TransactionID` worth checking out. This is also worth checking out, for the same reasons in the `purchases.csv` dataset.

    Analyzing relations between entities is natural in graph databases, compared to looking at columnar or transactional data like the above - this powers its fraud detection capabilities. This is because the entity-relations are directly represented ('index-free adjacency') as first-class structures in a graph database.

    Because relations / edges are first class structures, it models a higher level abstraction (network) closer to human activity, compared to columnar data. For example, in analyzing purchases, instead of joining the customer and purchases table, a graph that link customers to merchants (entities) via purchases (edges).

    In graph databases, it is trivial for properties (e.g. `CardNumber`) of a node to be 'promoted' into nodes, creating a data 'web' especially for categories that matter to the analysis. So instead of scanning every customer for `CardNumber`, the `Card` node can be a hub with related `Customer`s, `Purchase`s and `Merchant`s.

    Based on the initial investigation, use cases like ID collision, state flaws, fraud detection or merchant analytics can be possible next steps.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Duplicate transaction analysis

    As the initial exploration revealed something interesting, the next steps would be to examine the possible reasons for the duplicate transactions, whether fraud can be immediately ruled out, or further graph analysis is required.
    """)
    return


@app.cell
def _(purchases):
    # Pull every row that shares a non-unique transaction_id
    duplicate_purchases = purchases[purchases.duplicated(subset=['TransactionID'], keep=False)]

    # Sort to compare side-by-side
    duplicate_purchases = duplicate_purchases.sort_values(by='TransactionID')

    duplicate_purchases # ignore the unnamed column - a marimo artifact.
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Examining duplicate purchases reveal no immediate pattern - the duplicate transactions are uniformly distributed in time and amount. 27 out of 30 merchants and 54 out of 100 cards are involved.

    Purchase data on its own is less useful, and enrichment of this by adding context - `Customer -> Card -> Purchase -> Merchant` would provide a more valuable analysis.

    This is also challenging to analyse transaction-by-transaction, so a graph data science approach of finding possible sub-communities engaging in fraudulent activity can be used.
    """)
    return


@app.cell
def _(transfers):
    # same for duplicate transfers
    duplicate_transfers = transfers[transfers.duplicated(subset=['TransactionID'], keep=False)]
    duplicate_transfers
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For the duplicate `TransactionID`, it appears to be completely different transcations - so possibly a glitch that needs to be flagged for a system investigation.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Graph Data Modeling and Data Ingestion
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(f"""
    ## Graph Data Model

    Based on the initial exploration and subsequent questions, the proposed model would need as entities, because we consider them significant: 

    - Customer
    - Merchant
    - Card
    - Account
    - Transfer
    - Purchase

    ### Proposed Core Model

    {mo.image(src="public/banking.png")}

    [Source](https://arrows.app/#/import/json=eyJncmFwaCI6eyJzdHlsZSI6eyJmb250LWZhbWlseSI6InNhbnMtc2VyaWYiLCJiYWNrZ3JvdW5kLWNvbG9yIjoiI2ZmZmZmZiIsImJhY2tncm91bmQtaW1hZ2UiOiIiLCJiYWNrZ3JvdW5kLXNpemUiOiIxMDAlIiwibm9kZS1jb2xvciI6IiNmZmZmZmYiLCJib3JkZXItd2lkdGgiOjQsImJvcmRlci1jb2xvciI6IiMwMDAwMDAiLCJyYWRpdXMiOjUwLCJub2RlLXBhZGRpbmciOjUsIm5vZGUtbWFyZ2luIjoyLCJvdXRzaWRlLXBvc2l0aW9uIjoiYXV0byIsIm5vZGUtaWNvbi1pbWFnZSI6IiIsIm5vZGUtYmFja2dyb3VuZC1pbWFnZSI6IiIsImljb24tcG9zaXRpb24iOiJpbnNpZGUiLCJpY29uLXNpemUiOjY0LCJjYXB0aW9uLXBvc2l0aW9uIjoiaW5zaWRlIiwiY2FwdGlvbi1tYXgtd2lkdGgiOjIwMCwiY2FwdGlvbi1jb2xvciI6IiMwMDAwMDAiLCJjYXB0aW9uLWZvbnQtc2l6ZSI6NTAsImNhcHRpb24tZm9udC13ZWlnaHQiOiJub3JtYWwiLCJsYWJlbC1wb3NpdGlvbiI6Imluc2lkZSIsImxhYmVsLWRpc3BsYXkiOiJwaWxsIiwibGFiZWwtY29sb3IiOiIjMDAwMDAwIiwibGFiZWwtYmFja2dyb3VuZC1jb2xvciI6IiNmZmZmZmYiLCJsYWJlbC1ib3JkZXItY29sb3IiOiIjMDAwMDAwIiwibGFiZWwtYm9yZGVyLXdpZHRoIjo0LCJsYWJlbC1mb250LXNpemUiOjQwLCJsYWJlbC1wYWRkaW5nIjo1LCJsYWJlbC1tYXJnaW4iOjQsImRpcmVjdGlvbmFsaXR5IjoiZGlyZWN0ZWQiLCJkZXRhaWwtcG9zaXRpb24iOiJpbmxpbmUiLCJkZXRhaWwtb3JpZW50YXRpb24iOiJwYXJhbGxlbCIsImFycm93LXdpZHRoIjo1LCJhcnJvdy1jb2xvciI6IiMwMDAwMDAiLCJtYXJnaW4tc3RhcnQiOjUsIm1hcmdpbi1lbmQiOjUsIm1hcmdpbi1wZWVyIjoyMCwiYXR0YWNobWVudC1zdGFydCI6Im5vcm1hbCIsImF0dGFjaG1lbnQtZW5kIjoibm9ybWFsIiwicmVsYXRpb25zaGlwLWljb24taW1hZ2UiOiIiLCJ0eXBlLWNvbG9yIjoiIzAwMDAwMCIsInR5cGUtYmFja2dyb3VuZC1jb2xvciI6IiNmZmZmZmYiLCJ0eXBlLWJvcmRlci1jb2xvciI6IiMwMDAwMDAiLCJ0eXBlLWJvcmRlci13aWR0aCI6MCwidHlwZS1mb250LXNpemUiOjE2LCJ0eXBlLXBhZGRpbmciOjUsInByb3BlcnR5LXBvc2l0aW9uIjoib3V0c2lkZSIsInByb3BlcnR5LWFsaWdubWVudCI6ImNvbG9uIiwicHJvcGVydHktY29sb3IiOiIjMDAwMDAwIiwicHJvcGVydHktZm9udC1zaXplIjoxNiwicHJvcGVydHktZm9udC13ZWlnaHQiOiJub3JtYWwifSwibm9kZXMiOlt7ImlkIjoibjIiLCJwb3NpdGlvbiI6eyJ4IjoyNDYuNDg1OTk3Mzk1NjAxLCJ5IjotNDgxLjc4NzQ2NDM3Nzg1Njg1fSwiY2FwdGlvbiI6IkNhcmQiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fSx7ImlkIjoibjQiLCJwb3NpdGlvbiI6eyJ4Ijo2MjMuNjA4NzE3MDk4ODg2MSwieSI6LTI4OC44MjI0NzgxOTA2NjA2fSwiY2FwdGlvbiI6IlRyYW5zZmVyIiwic3R5bGUiOnt9LCJsYWJlbHMiOltdLCJwcm9wZXJ0aWVzIjp7fX0seyJpZCI6Im41IiwicG9zaXRpb24iOnsieCI6LTUzLjU1MjQyNjI1MzUyNDg4NSwieSI6LTY3MC41MTA2NzIyNzk1NTI5fSwiY2FwdGlvbiI6Ik1lcmNoYW50ICIsInN0eWxlIjp7fSwibGFiZWxzIjpbXSwicHJvcGVydGllcyI6e319LHsiaWQiOiJuNiIsInBvc2l0aW9uIjp7IngiOjYyMy42MDg3MTcwOTg4ODYxLCJ5IjotNjcwLjUxMDY3MjI3OTU1Mjl9LCJjYXB0aW9uIjoiUHVyY2hhc2UiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fSx7ImlkIjoibjciLCJwb3NpdGlvbiI6eyJ4IjotNTMuNTUyNDI2MjUzNTI0ODg1LCJ5IjotNDgxLjc4NzQ2NDM3Nzg1Njg1fSwiY2FwdGlvbiI6IkN1c3RvbWVyIiwic3R5bGUiOnt9LCJsYWJlbHMiOltdLCJwcm9wZXJ0aWVzIjp7fX0seyJpZCI6Im44IiwicG9zaXRpb24iOnsieCI6MjQ2LjQ4NTk5NzM5NTYwMSwieSI6LTI4OC44MjI0NzgxOTA2NjA2fSwiY2FwdGlvbiI6IkFjY291bnQiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fV0sInJlbGF0aW9uc2hpcHMiOlt7ImlkIjoibjgiLCJ0eXBlIjoiUEFJRF9UTyIsInN0eWxlIjp7fSwicHJvcGVydGllcyI6e30sInRvSWQiOiJuNSIsImZyb21JZCI6Im42In0seyJpZCI6Im45IiwidHlwZSI6IkZVTkRTIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjIiLCJ0b0lkIjoibjYifSx7ImlkIjoibjEwIiwidHlwZSI6IkhBU19DQVJEIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjciLCJ0b0lkIjoibjIifSx7ImlkIjoibjExIiwidHlwZSI6IkhBU19BQ0NPVU5UIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjciLCJ0b0lkIjoibjgifSx7ImlkIjoibjEyIiwidHlwZSI6IlNFTlRfVE8iLCJzdHlsZSI6e30sInByb3BlcnRpZXMiOnt9LCJmcm9tSWQiOiJuOCIsInRvSWQiOiJuNCJ9LHsiaWQiOiJuMTMiLCJ0eXBlIjoiUkVDRUlWRURfQlkiLCJzdHlsZSI6e30sInByb3BlcnRpZXMiOnt9LCJmcm9tSWQiOiJuNCIsInRvSWQiOiJuOCJ9XX0sImRpYWdyYW1OYW1lIjoiYmFua2luZyJ9)

    ### Model Constraints

    Neo4j supports four constraint kinds: uniqueness, existence, node/edge key (combo of uniqueness and existence) and type. Constraints automatically create backing indexes that help speed up MATCH operations.

    `Customer.CIF, Card.CardNumber, Account.AccountNumber` are unique
    Merchant names are unique (assumed)

    `TransactionID` is not unique, so either we create a synthetic key (supports idempotent loads) or use CREATE instead of MERGE (simplicity).

    ---

    ### Use cases

    The identified use cases are:

    1. ID Collisions/Fraud
    2. Merchant analytics

    Questions for ID Collisions/Fraud

    1. Why are `purchases['TransactionID']` not unique?
    2. Which cards/customers made purchases that are associated with duplicate `TransactionID`s?
    3. Why is there a non-unique TransactionID in `transfers`?
    4. Which customers' transfers are associated with duplicate `TransactionID`s?

    Questions for Merchant analytics

    1. Which occupation dominates per merchant?
    2. Which merchants serve the youngest vs oldest customers?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Load Data
    """)
    return


@app.cell
def _(GraphDatabase):
    # using CE, cannot CREATE

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    driver.verify_connectivity()

    # clean slate
    with driver.session() as _s:
        _s.run("MATCH (n) DETACH DELETE n")
    return (driver,)


@app.cell
def _(driver):
    # Create constraints
    # Transaction IDs are supposed to be constraints, but for this analysis, we need to load them as dupes

    constraints = [
        "CREATE CONSTRAINT customer_cif IF NOT EXISTS FOR (c:Customer) REQUIRE c.cif IS UNIQUE",
        "CREATE CONSTRAINT card_number IF NOT EXISTS FOR (c:Card) REQUIRE c.cardNumber IS UNIQUE",
        "CREATE CONSTRAINT account_number IF NOT EXISTS FOR (a:Account) REQUIRE a.accountNumber IS UNIQUE",
        "CREATE CONSTRAINT merchant_name IF NOT EXISTS FOR (m:Merchant) REQUIRE m.name IS UNIQUE",
    ]

    with driver.session() as _s:
        for c in constraints:
            _s.run(c)
    return


@app.cell
def _(customers, driver):
    # Load Customers, Cards and Accounts

    _rows = customers.to_dict("records")
    _q = """
    UNWIND $rows AS row
    MERGE (c:Customer {cif: row.CIF})
      SET c.age = row.Age, c.firstName = row.FirstName, c.lastName = row.LastName,
          c.email = row.EmailAddress, c.phone = row.PhoneNumber, c.gender = row.Gender,
          c.address = row.Address, c.country = row.Country, c.jobTitle = row.JobTitle
    MERGE (card:Card {cardNumber: row.CardNumber})
    MERGE (acct:Account {accountNumber: row.AccountNumber})
    MERGE (c)-[:HAS_CARD]->(card)
    MERGE (c)-[:HAS_ACCOUNT]->(acct)
    """
    with driver.session() as _s:
        _s.run(_q, rows=_rows)        
    return


@app.cell
def _(driver, purchases):
    # Load Merchants

    _names = [{"name": n} for n in purchases["Merchant"].unique().tolist()]
    with driver.session() as _s:
        _s.run("UNWIND $rows AS row MERGE (:Merchant {name: row.name})", rows=_names)
    return


@app.cell
def _(driver, purchases):
    # Load Purchases; note - create node & attach to existing card + merchant.

    _df = purchases.copy()
    _df["PurchaseDatetime"] = _df["PurchaseDatetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    _rows = _df.to_dict("records")

    _q = """
    UNWIND $rows AS row
    MATCH (card:Card {cardNumber: row.CardNumber})
    MATCH (m:Merchant {name: row.Merchant})
    CREATE (p:Purchase {
        transactionId: row.TransactionID,
        amount: row.Amount,
        purchaseDatetime: datetime(row.PurchaseDatetime),
        cardIssuer: row.CardIssuer
    })
    CREATE (card)-[:FUNDS]->(p)
    CREATE (p)-[:PAID_TO]->(m)
    """

    with driver.session() as _s:
        for _i in range(0, len(_rows), 1000):          # batch of 1000
            _s.run(_q, rows=_rows[_i:_i+1000])
    return


@app.cell
def _(driver, transfers):
    # Load Transfers; note - create node, attach sender + receiver

    _df = transfers.copy()
    _df["TransferDatetime"] = _df["TransferDatetime"].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
    _rows = _df.to_dict("records")

    _q = """
    UNWIND $rows AS row
    MATCH (sender:Account {accountNumber: row.SenderAccountNumber})
    MATCH (receiver:Account {accountNumber: row.ReceiverAccountNumber})
    CREATE (t:Transfer {
        transactionId: row.TransactionID,
        amount: row.Amount,
        transferDatetime: datetime(row.TransferDatetime)
    })
    CREATE (sender)-[:SENT_TO]->(t)
    CREATE (t)-[:RECEIVED_BY]->(receiver)
    """

    with driver.session() as _s:
        _s.run(_q, rows=_rows)
    return


@app.cell
def _(driver):
    # Verify

    with driver.session() as _s:
        counts = _s.run("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label
        """).data()
    counts
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Cypher Query Development
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Duplicate Transaction study
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Why are `purchases['TransactionID']` not unique?

    One of the angles is to observe - of the 42 duplicate purchases, are the amounts the same? This query looks at all purchases where transaction and purchase amount are identical.

    `collect(p)` performs the 'collecting' of duplicates into 1 row and `count(p)` counts the number of duplicate rows.
    """)
    return


@app.cell
def _(driver, pd):
    _q = """
    MATCH (p:Purchase)
    // Group by BOTH transactionId and amount
    WITH p.transactionId AS txId, p.amount AS purchaseAmount, collect(p) AS duplicateNodes, count(p) AS count
    // Filter for groups that have more than one identical node
    WHERE count > 1
    RETURN txId, purchaseAmount, count, duplicateNodes
    ORDER BY count DESC;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()

    _result = pd.DataFrame(_o)
    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There are no duplicate purchases with identical amounts.

    ### Which cards/customers made purchases that are associated with duplicate TransactionIDs?

    This query expands `purchase` context by finding associated customers and merchants (MATCH). Groups all purchase rows by txid and collects distinct CIFs associated with purchase.

    if size(customers) is 1, all duplicate purchases are from same customer/card. Possible replay attack/fraud because same person's card shows the same transcation ID more than once.

    if size(customers) is n (i.e. each duplicate txid belongs to a different customer), this could indicate an ID collision, or non-fraud related unintentional system issue.
    """)
    return


@app.cell
def _(driver, pd):
    _q = """
    MATCH (cust:Customer)-[:HAS_CARD]->(card:Card)-[:FUNDS]->(p:Purchase)-[:PAID_TO]->(m:Merchant)
    WITH p.transactionId AS txid, collect(DISTINCT cust.cif) AS customers, count(*) AS n
    WHERE n > 1
    RETURN txid, n, customers, size(customers) AS distinctCustomers
    ORDER BY distinctCustomers
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()

    _result = pd.DataFrame(_o)
    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Of the 42 duplicates, only transcation ID 401743 is confined to a single card/customer - a collision worth inspecting.
    """)
    return


@app.cell
def _(driver, pd):
    # zoom in to cif = 5 on the duplicate transaction.

    _q = """
    MATCH (c:Customer {cif: "5"})-[:HAS_CARD]->(a:Card)-[:FUNDS]->(p:Purchase {transactionId: "401743"})-[:PAID_TO]->(m:Merchant)
    RETURN p.transactionId, c.firstName, c.lastName, m.name, p.amount, p.purchaseDatetime, a.cardNumber, p.cardIssuer;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()

    _result = pd.DataFrame(_o)
    _result['p.purchaseDatetime'] = pd.to_datetime(_result['p.purchaseDatetime'].apply(lambda x: x.iso_format() if pd.notnull(x) else None))

    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Both are in near-equal amounts. Given two different merchants → does not appear to be a clean replay of transaction.

    We can then turn to look into the transactions of this person of interest.
    """)
    return


@app.cell
def _(driver, pd):
    # could cif = 5 be a POI? let's see his transcation history

    _q = """
    MATCH (c:Customer {cif: "5"})-[:HAS_CARD]->(a:Card)-[:FUNDS]->(p:Purchase)-[:PAID_TO]->(m:Merchant)
    RETURN c.cif, p.transactionId, m.name, p.amount, p.purchaseDatetime, a.cardNumber, p.cardIssuer;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()

    _result = pd.DataFrame(_o)
    _result['p.purchaseDatetime'] = pd.to_datetime(_result['p.purchaseDatetime'].apply(lambda x: x.iso_format() if pd.notnull(x) else None))
    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    There are 178 transactions for customer 5, 'Erick Ingram'.
    He makes considerable high value transactions (similar to the rest of the customers).
    All his transactions are spread rather uniformly in the snapshot.
    All his transactions are made to the 30 unique merchants in the dataset (possibly synthetic).

    Conclusion: duplicates are ID collisions across distinct customers, not replay/takeover.

    Benefits of graph database:
    - Accessing customer, purchase, merchant, card details in one efficient, logical query (multiple joins would be required in RDBMS)

    Possible next steps:
    - Find out with bank, the reasons behind multiple card issuer for each card.
    - Check with bank for transfer transaction race-conditions (see below cell)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Why is there a non-unique TransactionID in transfers?
    ### Which customers' transfers are associated with duplicate TransactionIDs?

    It appears a genuine encoding issue with transaction id, because the transfers occured to 4 separate customers with differing amounts.
    """)
    return


@app.cell
def _(driver, pd):
    # note undirected relationship

    _q = """
    MATCH (c:Customer)-[:HAS_ACCOUNT]->(a:Account)-[:SENT_TO | RECEIVED_BY]-(t:Transfer {transactionId: "835422"})
    RETURN t.transactionId, c.cif, c.lastName, c.firstName, t.amount, t.transferDatetime;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()

    _result = pd.DataFrame(_o)
    _result['t.transferDatetime'] = pd.to_datetime(_result['t.transferDatetime'].apply(lambda x: x.iso_format() if pd.notnull(x) else None))
    _result
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Merchant analytics

    ### Which occupation dominates each merchant's customer base?
    """)
    return


@app.cell
def _(alt, driver, mo, pd):
    _q = """
    MATCH (cust:Customer)-[:HAS_CARD]->(:Card)-[:FUNDS]->(p:Purchase)-[:PAID_TO]->(m:Merchant)
    WITH m, cust.jobTitle AS job, count(*) AS n
    ORDER BY n DESC
    WITH m, collect({job: job, n: n})[0] AS top, sum(n) AS total
    RETURN m.name AS merchant, top.job AS dominantOccupation,
           round(100.0 * top.n / total) AS sharePct
    ORDER BY sharePct DESC
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _result = pd.DataFrame(_o)

    _chart = (
        alt.Chart(_result)
        .mark_bar()
        .encode(
            x=alt.X("sharePct:Q",
                    title="Top occupation's share of the merchant's customers (%)"),
            y=alt.Y("merchant:N", sort="-x", title="Merchant"),
            color=alt.Color("dominantOccupation:N", title="Dominant occupation"),
            tooltip=["merchant", "dominantOccupation", "sharePct"],
        )
        .properties(height=520, title="Most common occupation per merchant (note: shares are low)")
    )
    mo.ui.altair_chart(_chart)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Age skew: which merchants serve the youngest vs oldest customers?
    """)
    return


@app.cell
def _(alt, driver, mo, pd):
    _q = """
    MATCH (cust:Customer)-[:HAS_CARD]->(:Card)-[:FUNDS]->(p:Purchase)-[:PAID_TO]->(m:Merchant)
    RETURN m.name AS merchant,
           round(percentileCont(cust.age, 0.5)) AS medianAge,
           count(p) AS txns
    ORDER BY medianAge
    """
    with driver.session() as _s:
        _o = _s.run(_q).data()

    _age = pd.DataFrame(_o)

    _chart = (
        alt.Chart(_age)
        .mark_circle(size=110, opacity=0.85)
        .encode(
            x=alt.X("medianAge:Q",
                    title="Median customer age",
                    scale=alt.Scale(zero=False, nice=False,
                                    domain=[_age.medianAge.min() - 1,
                                            _age.medianAge.max() + 1])),
            y=alt.Y("merchant:N", sort="-x", title="Merchant"),
            tooltip=["merchant", "medianAge", "txns"],
        )
        .properties(height=520,
                    title="Median customer age per merchant (zoomed axis — spread is only ~2 yrs)")
    )
    mo.ui.altair_chart(_chart)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The results are quite uniform, indicating possible synthetic data.
    - Age spread of customers per unique merchant is 2 years (between 52 to 54yo)
    - The merchant shares per occupation is uniform

    The benefit of cypher
    - Analytics and summary statistics in a single query spanning multiple entities and relations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Graph Data Science
    """)
    return


@app.cell
def _(driver):
    # check GDS installed
    with driver.session() as _s:
        _o = _s.run("RETURN gds.version()").data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Community Detection

    The following runs a GDS community detection algorithm by

    1. Finding a subgraph of transfers (`MATCH`), and storing in a projection (`xfer`)
    2. Only store the senders and receivers (`s, r`) and transfer amounts (tr.amount) in `xfer`
    3. transfer amount is used as relationship weight (how important the relationship is)
    """)
    return


@app.cell
def _(driver):
    _q = """
    MATCH (s:Account)-[:SENT_TO]->(tr:Transfer)-[:RECEIVED_BY]->(r:Account)
    RETURN gds.graph.project(
      'xfer',
      s,
      r,
      { relationshipProperties: { weight: tr.amount } }
    ) AS g;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Projection is correct — 100 nodes, 1000 relationships, matching the full transfer set. The graph xfer is now in memory and ready.

    ### WCC - Weakly Connected Components

    GDS WCC algorithm performs the following:
    1. Look for 'islands' of accounts - rings that traded money with each other only and assign componentId to that island
    2. Return ID, size of island and up to 10 `accountNumber`s of that island
    """)
    return


@app.cell
def _(driver):
    _q = """
    CALL gds.wcc.stream('xfer') YIELD nodeId, componentId
    RETURN componentId, count(*) AS size,
           collect(gds.util.asNode(nodeId).accountNumber)[..10] AS sample
    ORDER BY size ASC;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    One component, all 100 accounts — no isolated sub-networks. Every account is reachable from every other through transfer flow. This rules out the cleanest fraud pattern (rings of accounts transacting only among themselves). But we can confirm
    if there are roundtripping occuring within this big component by running a cycle detection query (See [below](#finding-roundtripping-transfers)).

    Note:

    One row, size 100 → single giant component, no isolated rings. Given this near-uniform network; it rules out the "island of accounts only transacting among themselves" fraud pattern.

    Multiple rows, especially small ones (size 2–6) → those small components are immediately interesting — a handful of accounts cut off from the main flow is exactly the structure cycle/mule analysis looks for. Flag any of those for follow-up.

    ### Louvain

    GDS also provides Louvain algorithm that finds tight sub-community/network (weights included) within the WCC islands (no weight, just reachability).
    """)
    return


@app.cell
def _(driver):
    # Louvain to look for tight sub-communities within whatever WCC returns — that's where the weak-vs-real structure signal shows up via the modularity score.

    _q = """
    CALL gds.louvain.stream('xfer', { relationshipWeightProperty: 'weight' })
    YIELD nodeId, communityId
    RETURN communityId, count(*) AS members,
           collect(gds.util.asNode(nodeId).accountNumber)[..10] AS sample
    ORDER BY members DESC;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Modularity scores of Louvain measure how well the algorithm could partition the graph. It is a global measure, not an individual community evaluation.
    """)
    return


@app.cell
def _(driver):
    # Compute modularity score

    _q = """
    CALL gds.louvain.stats('xfer', { relationshipWeightProperty: 'weight' })
    YIELD communityCount, modularity, modularities
    RETURN communityCount, modularity;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Modularity 0.15 ≲ 0.3 → communities are weak/arbitrary; the partition is essentially noise. So no meaningful community structure in the transfer graph at this snapshot.

    So the transfer network shows no community structure or isolated components; recommend to include other forms of monitoring (e.g. transaction-level) on top of network analysis for this dataset.

    Benefits of GDS
    - Run complex datascience network algorithms: apply mathematically rigourous methods exclusive to graph data for insights
    - Built in : exactly where the data sits for lower latency, higher performance.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Extra: Finding roundtripping transfers

    We need to cycles and track the time of transactions, because roundtripping fraud is time-ordered.

    ### Direct "ping-pong"
    """)
    return


@app.cell
def _(driver):
    _q = """
    MATCH (a:Account)-[:SENT_TO]->(t1:Transfer)-[:RECEIVED_BY]->(b:Account),
          (b)-[:SENT_TO]->(t2:Transfer)-[:RECEIVED_BY]->(a)
    WHERE a.accountNumber < b.accountNumber        // dedupe A-B / B-A
      AND t2.transferDatetime > t1.transferDatetime
      AND t2.transferDatetime <= t1.transferDatetime + duration('P3D')  // "closes the loop" quickly
    RETURN a.accountNumber AS acctA, b.accountNumber AS acctB,
           t1.transactionId AS out_tx, t1.amount AS out_amt, t1.transferDatetime AS out_time,
           t2.transactionId AS return_tx, t2.amount AS return_amt, t2.transferDatetime AS return_time,
           abs(t1.amount - t2.amount) AS amountDelta
    ORDER BY amountDelta ASC, out_time ASC;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    No results - hence, there are no simple, common cases of "ping pong" transfers - account A -> B, and back to -> A.

    ### Variable length, N-hops (A->B->C->...->A) with intermediate account revisit

    This is the layering of several accounts before returning to origin for paths between 4 and 12 relationships, or 2 and 6 transfers inclusive (each transfer being 2 relationships).
    """)
    return


@app.cell
def _(driver):
    _q = """
    MATCH path = (a:Account)-[:SENT_TO|RECEIVED_BY*4..12]->(a)
    WITH path, a,
         [n IN nodes(path) WHERE n:Transfer] AS transfers
    WHERE length(path) % 2 = 0                                   // ends on an Account, not mid-Transfer
      AND all(i IN range(0, size(transfers)-2)
              WHERE transfers[i].transferDatetime <= transfers[i+1].transferDatetime)  // money can't flow backward in time
      AND duration.between(transfers[0].transferDatetime, transfers[-1].transferDatetime).days <= 7
    RETURN a.accountNumber AS originAccount,
           [t IN transfers | t.transactionId] AS txChain,
           [t IN transfers | t.amount] AS amounts,
           [t IN transfers | t.transferDatetime] AS times,
           abs(transfers[0].amount - transfers[-1].amount) AS amountDrift
    ORDER BY size(txChain) ASC, amountDrift ASC
    LIMIT 25;
    """

    with driver.session() as _s:
        _o = _s.run(_q).data()
    _o
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    25 potential roundtripping cycles (of up to 6 transfer hops) were identified. Cycles may occur naturally, so further investigation is required. Options include:

    - Scoring and ranking suspicious accounts
    - Enriching account information for context
    - Cross-referencing other signals (e.g. duplicate transactions)
    - Human intervention

    Notes:

    This query can be simplified and sped up by adding a new, direct edge `TRANSFERRED` to Accounts - `(Account)-[:TRANSFERRED {transactionId, amount, transferDatetime}]->(Account)`, which would simplify to

    ```cypher
    MATCH path = (a:Account)-[:TRANSFERRED*2..6]->(a)
    WHERE all(i IN range(0, size(relationships(path))-2)
    WHERE relationships(path)[i].transferDatetime <= relationships(path)[i+1].transferDatetime)
    RETURN a, relationships(path)
    ```
    """)
    return


@app.cell
def _(driver):
    # cleanup, failIfMissing = false (acts like IF EXISTS)
    with driver.session() as _s:
        _o = _s.run("CALL gds.graph.drop('xfer', false) YIELD graphName;").data()
    _o
    return


if __name__ == "__main__":
    app.run()
