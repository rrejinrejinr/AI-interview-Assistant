# Relational Databases & SQL Optimization

## What is SQL (Structured Query Language)
SQL (Structured Query Language) is the domain-specific standard language used to store, manipulate, query, and manage data in Relational Database Management Systems (RDBMS) such as PostgreSQL, MySQL, SQLite, and Oracle.

Core SQL Commands:
- DDL (Data Definition Language): `CREATE`, `ALTER`, `DROP`, `TRUNCATE`
- DML (Data Manipulation Language): `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- DCL (Data Control Language): `GRANT`, `REVOKE`
- TCL (Transaction Control Language): `COMMIT`, `ROLLBACK`, `SAVEPOINT`

## SQL Joins: Combining Data from Multiple Tables
SQL Joins combine rows from two or more tables based on a related column between them:
1. `INNER JOIN`: Returns only rows with matching values in both tables.
   `SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id;`
2. `LEFT JOIN` (LEFT OUTER JOIN): Returns all rows from the left table, and matched rows from the right table (NULL if no match).
3. `RIGHT JOIN` (RIGHT OUTER JOIN): Returns all rows from the right table, and matched rows from the left table.
4. `FULL OUTER JOIN`: Returns all rows when there is a match in either left or right table.
5. `CROSS JOIN`: Returns the Cartesian product of all rows.

## Indexing Fundamentals
Indexes are auxiliary data structures (predominantly B-Trees) that accelerate search queries from O(N) sequential table scans to O(log N) lookups.
- Single-column indexes: Optimize filters on high-cardinality columns.
- Composite indexes: Optimize multi-column filtering; order of columns must match query predicates (Leftmost Prefix Rule).
- Over-indexing warning: Indexes add write overhead during `INSERT`, `UPDATE`, and `DELETE` operations.

## ACID Transactions
- Atomicity: All operations in a transaction succeed, or the entire transaction is rolled back.
- Consistency: The database transitions only between valid states conforming to schema constraints.
- Isolation: Concurrent transactions do not interfere with each other (Read Committed, Repeatable Read, Serializable).
- Durability: Committed transactions persist permanently in non-volatile storage (WAL / Write-Ahead Logging).
