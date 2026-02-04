# Technical Specification: Search Index

## Scope
Full-text search index for documents.

## Components
- Indexer (batch and incremental)
- Query API (REST)
- Ranking model

## Constraints
- Latency p95 < 200ms
- Index size < 2x raw size
