# /// script
# dependencies = [
#     "marimo",
#     "neo4j==6.2.0",
#     "pandas==3.0.3",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd

    from neo4j import GraphDatabase

    return GraphDatabase, mo, pd


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


@app.cell
def _(pd, purchases):
    purchases['TransactionID'] = purchases['TransactionID'].astype(str)
    purchases['PurchaseDatetime'] = pd.to_datetime(purchases['PurchaseDatetime'], format='ISO8601')
    purchases
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
    This set of data appears to be a snapshot from an analytical database between Jan 1 2021 and Sep 7 2021. When importing the data, some columns were casted into proper types for more accurate analysis.

    `customers.csv` contains details about banking customers. There are 100 customers (unique rows), and can be represented as nodes/vertices in neo4j. The uniqueness of identity would make it challenging to identify classic fraud signals like mule networks, so extra steps like watching behaviour over time would be required. But the availability of demographic data would be useful for merchant analytics, like age and occupation.

    `purchases.csv` contains details of 10,000 transcations with a set of 30 merchants made through the customers' card. Transactions here imply flow of credit from customer to merchant - this can be represented as directed edges/relationships in neo4j. To find out who made the purchase, `CardNumber` needs to be joined with the `customer` table.
    There are 42 duplicate `TranscationID`s - this is a **red flag** for potential replay attacks, exploits or account takeovers - or some accidental system issue (double clicking, etc). This is worth checking out.

    `transfers` contains details of 1,000 credit transfers between customer accounts. This can be represented as a sending-to or receive-from relationship/edge in neo4j. Similarly, there is one non-unique `TransactionID` worth checking out, from the summary statistics. This is also worth checking out.

    To uncover patterns of fraud, it is often beneficial to analyze the relations between entities, compared to looking at columnar or transactional data like the above. This is because the entity-relations are directly represented ('index-free adjacency') as first-class structures in a graph database like neo4j.

    Because relations / edges are first class structures, it models a higher level abstraction (network) closer to human activity, compared to columnar data. For example, in analyzing purchases, instead of joining the customer and purchases table, a graph that link customers to merchants (entities) via purchases (edges).

    In graph databases, it is trivial for properties (e.g. `country`) of a node to be 'promoted' into nodes, creating a data 'web' especially for categories that matter to the analysis. So instead of scanning every customer for `country`, the `country` node can be a hub with `customer`s pointing to it.

    Based on the initial investigation, use cases like fraud detection can be possible next steps.
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
    # Graph Data Modeling and Data Ingestion
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(f"""
    ## Graph Data Model

    ### Domain

    This dataset is a banking customer dataset, summarised in the preceding section.

    Let us load the core graph for single source of truth, using real-world business entities.

    The core graph will evolve as more use-cases emerge.

    ### Core use case - banking

    1. Show all transactions relating to account.
    2. Which merchants does account purchase from most?
    3. Show all funds received from other accounts.
    4. Show all funds transferred to other accounts.

    ### Proposed Core Model

    {mo.image(src="public/banking.png")}

    [Source](https://arrows.app/#/import/json=eyJncmFwaCI6eyJzdHlsZSI6eyJmb250LWZhbWlseSI6InNhbnMtc2VyaWYiLCJiYWNrZ3JvdW5kLWNvbG9yIjoiI2ZmZmZmZiIsImJhY2tncm91bmQtaW1hZ2UiOiIiLCJiYWNrZ3JvdW5kLXNpemUiOiIxMDAlIiwibm9kZS1jb2xvciI6IiNmZmZmZmYiLCJib3JkZXItd2lkdGgiOjQsImJvcmRlci1jb2xvciI6IiMwMDAwMDAiLCJyYWRpdXMiOjUwLCJub2RlLXBhZGRpbmciOjUsIm5vZGUtbWFyZ2luIjoyLCJvdXRzaWRlLXBvc2l0aW9uIjoiYXV0byIsIm5vZGUtaWNvbi1pbWFnZSI6IiIsIm5vZGUtYmFja2dyb3VuZC1pbWFnZSI6IiIsImljb24tcG9zaXRpb24iOiJpbnNpZGUiLCJpY29uLXNpemUiOjY0LCJjYXB0aW9uLXBvc2l0aW9uIjoiaW5zaWRlIiwiY2FwdGlvbi1tYXgtd2lkdGgiOjIwMCwiY2FwdGlvbi1jb2xvciI6IiMwMDAwMDAiLCJjYXB0aW9uLWZvbnQtc2l6ZSI6NTAsImNhcHRpb24tZm9udC13ZWlnaHQiOiJub3JtYWwiLCJsYWJlbC1wb3NpdGlvbiI6Imluc2lkZSIsImxhYmVsLWRpc3BsYXkiOiJwaWxsIiwibGFiZWwtY29sb3IiOiIjMDAwMDAwIiwibGFiZWwtYmFja2dyb3VuZC1jb2xvciI6IiNmZmZmZmYiLCJsYWJlbC1ib3JkZXItY29sb3IiOiIjMDAwMDAwIiwibGFiZWwtYm9yZGVyLXdpZHRoIjo0LCJsYWJlbC1mb250LXNpemUiOjQwLCJsYWJlbC1wYWRkaW5nIjo1LCJsYWJlbC1tYXJnaW4iOjQsImRpcmVjdGlvbmFsaXR5IjoiZGlyZWN0ZWQiLCJkZXRhaWwtcG9zaXRpb24iOiJpbmxpbmUiLCJkZXRhaWwtb3JpZW50YXRpb24iOiJwYXJhbGxlbCIsImFycm93LXdpZHRoIjo1LCJhcnJvdy1jb2xvciI6IiMwMDAwMDAiLCJtYXJnaW4tc3RhcnQiOjUsIm1hcmdpbi1lbmQiOjUsIm1hcmdpbi1wZWVyIjoyMCwiYXR0YWNobWVudC1zdGFydCI6Im5vcm1hbCIsImF0dGFjaG1lbnQtZW5kIjoibm9ybWFsIiwicmVsYXRpb25zaGlwLWljb24taW1hZ2UiOiIiLCJ0eXBlLWNvbG9yIjoiIzAwMDAwMCIsInR5cGUtYmFja2dyb3VuZC1jb2xvciI6IiNmZmZmZmYiLCJ0eXBlLWJvcmRlci1jb2xvciI6IiMwMDAwMDAiLCJ0eXBlLWJvcmRlci13aWR0aCI6MCwidHlwZS1mb250LXNpemUiOjE2LCJ0eXBlLXBhZGRpbmciOjUsInByb3BlcnR5LXBvc2l0aW9uIjoib3V0c2lkZSIsInByb3BlcnR5LWFsaWdubWVudCI6ImNvbG9uIiwicHJvcGVydHktY29sb3IiOiIjMDAwMDAwIiwicHJvcGVydHktZm9udC1zaXplIjoxNiwicHJvcGVydHktZm9udC13ZWlnaHQiOiJub3JtYWwifSwibm9kZXMiOlt7ImlkIjoibjIiLCJwb3NpdGlvbiI6eyJ4IjoyNDYuNDg1OTk3Mzk1NjAxLCJ5IjotNDgxLjc4NzQ2NDM3Nzg1Njg1fSwiY2FwdGlvbiI6IkNhcmQiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fSx7ImlkIjoibjQiLCJwb3NpdGlvbiI6eyJ4Ijo2MjMuNjA4NzE3MDk4ODg2MSwieSI6LTI4OC44MjI0NzgxOTA2NjA2fSwiY2FwdGlvbiI6IlRyYW5zZmVyIiwic3R5bGUiOnt9LCJsYWJlbHMiOltdLCJwcm9wZXJ0aWVzIjp7fX0seyJpZCI6Im41IiwicG9zaXRpb24iOnsieCI6LTUzLjU1MjQyNjI1MzUyNDg4NSwieSI6LTY3MC41MTA2NzIyNzk1NTI5fSwiY2FwdGlvbiI6Ik1lcmNoYW50ICIsInN0eWxlIjp7fSwibGFiZWxzIjpbXSwicHJvcGVydGllcyI6e319LHsiaWQiOiJuNiIsInBvc2l0aW9uIjp7IngiOjYyMy42MDg3MTcwOTg4ODYxLCJ5IjotNjcwLjUxMDY3MjI3OTU1Mjl9LCJjYXB0aW9uIjoiUHVyY2hhc2UiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fSx7ImlkIjoibjciLCJwb3NpdGlvbiI6eyJ4IjotNTMuNTUyNDI2MjUzNTI0ODg1LCJ5IjotNDgxLjc4NzQ2NDM3Nzg1Njg1fSwiY2FwdGlvbiI6IkN1c3RvbWVyIiwic3R5bGUiOnt9LCJsYWJlbHMiOltdLCJwcm9wZXJ0aWVzIjp7fX0seyJpZCI6Im44IiwicG9zaXRpb24iOnsieCI6MjQ2LjQ4NTk5NzM5NTYwMSwieSI6LTI4OC44MjI0NzgxOTA2NjA2fSwiY2FwdGlvbiI6IkFjY291bnQiLCJzdHlsZSI6e30sImxhYmVscyI6W10sInByb3BlcnRpZXMiOnt9fV0sInJlbGF0aW9uc2hpcHMiOlt7ImlkIjoibjgiLCJ0eXBlIjoiUEFJRF9UTyIsInN0eWxlIjp7fSwicHJvcGVydGllcyI6e30sInRvSWQiOiJuNSIsImZyb21JZCI6Im42In0seyJpZCI6Im45IiwidHlwZSI6IkZVTkRTIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjIiLCJ0b0lkIjoibjYifSx7ImlkIjoibjEwIiwidHlwZSI6IkhBU19DQVJEIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjciLCJ0b0lkIjoibjIifSx7ImlkIjoibjExIiwidHlwZSI6IkhBU19BQ0NPVU5UIiwic3R5bGUiOnt9LCJwcm9wZXJ0aWVzIjp7fSwiZnJvbUlkIjoibjciLCJ0b0lkIjoibjgifSx7ImlkIjoibjEyIiwidHlwZSI6IlNFTlRfVE8iLCJzdHlsZSI6e30sInByb3BlcnRpZXMiOnt9LCJmcm9tSWQiOiJuOCIsInRvSWQiOiJuNCJ9LHsiaWQiOiJuMTMiLCJ0eXBlIjoiUkVDRUlWRURfQlkiLCJzdHlsZSI6e30sInByb3BlcnRpZXMiOnt9LCJmcm9tSWQiOiJuNCIsInRvSWQiOiJuOCJ9XX0sImRpYWdyYW1OYW1lIjoiYmFua2luZyJ9)

    ### Model Constraints

    Neo4j only supports four constraint kinds: uniqueness, node-key, existence, and type. Constraints automatically create backing indexes that help speed up MATCH operations.

    Customer.CIF, Card.CardNumber, Account.AccountNumber are unique
    Merchant names are unique (assumed)

    TransactionID is not unique, so either we create a synthetic key (supports idempotent loads) or use CREATE instead of MERGE (simplicity).

    ---

    ### Use cases

    The identified use cases are:

    1. Fraud
    2. Mechant analytics

    Questions for Fraud

    1. Why are `purchases['TransactionID']` not unique?
    2. Which cards/customers made purchases that are associated with duplicate transactionIDs?
    3. Why is there a non-unique TransactionID in `transfers`?
    4. Which customers' transfers are associated with duplicate transactionIDs?

    Questions for Mechant analytics

    1. Who are the youngest customers
    2. Oldest customers?
    3. Which age group spends the most?
    4. Occupation?
    """)
    return


@app.cell
def _(GraphDatabase):
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    driver.verify_connectivity()
    return (driver,)


@app.cell
def _(driver):
    # Create constraints

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


@app.cell
def _(driver):
    driver.session().close()
    return


if __name__ == "__main__":
    app.run()
