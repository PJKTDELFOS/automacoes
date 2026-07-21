# APPA Licitações

> **Production-grade ETL platform** for collecting, processing and
> delivering Brazilian public procurement opportunities from the PNCP.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Django](https://img.shields.io/badge/Django-5.x-success)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production-336791)

------------------------------------------------------------------------

# Overview

APPA is a production ETL platform designed to automate the complete
lifecycle of monitoring Brazilian public procurement opportunities.

The platform collects procurement notices from the Brazilian National
Public Procurement Portal (PNCP), validates, deduplicates, processes,
stores and distributes opportunities to subscribed customers
automatically.

The project was born from more than twelve years of experience in
Brazilian public procurement and evolved into a production system
focused on automation, scalability and resilience.

------------------------------------------------------------------------

# Features

-   Automated procurement collection
-   Intelligent deduplication
-   Parallel processing
-   PostgreSQL persistence
-   Customer-specific filtering
-   Excel report generation
-   Automated e-mail delivery
-   Retry engine
-   Persistent progress tracking
-   Structured logging
-   Docker deployment
-   Django administration

------------------------------------------------------------------------

# Architecture

``` text
             PNCP API
                │
                ▼
      Selenium Collection Engine
                │
                ▼
          ETL Processing
                │
                ▼
          PostgreSQL Database
                │
      ┌─────────┴─────────┐
      ▼                   ▼
 Analysis Engine   Campaign Engine
      │                   │
      └─────────┬─────────┘
                ▼
        Excel Report Engine
                │
                ▼
          Email Delivery
```

------------------------------------------------------------------------

# Technology Stack

## Backend

-   Python
-   Django
-   PostgreSQL
-   Selenium
-   Docker
-   Gunicorn
-   Nginx

## Libraries

-   Pandas
-   OpenPyXL
-   Psycopg2
-   Requests
-   ThreadPoolExecutor

## Infrastructure

-   Ubuntu Linux
-   Docker Compose
-   HTTPS
-   Cron Jobs

------------------------------------------------------------------------

# Production Metrics

  Metric             Value
  ------------------ ---------------
  Daily records      4,000--5,000
  Monthly records    \~150,000
  Annual records     \~1.8 million
  Parallel workers   5
  Database           PostgreSQL
  Deployment         Docker

------------------------------------------------------------------------

# Project Structure

``` text
appa/
appa_bot/
engine_busca_pncp/
engine_analise/
engine_campanha/
clientes/
utilitarios/
tests/

Dockerfile
docker-compose.yml
requirements.txt
```

------------------------------------------------------------------------

# Engineering Highlights

## Parallel Collection

The collection engine processes multiple pages concurrently using
ThreadPoolExecutor while preventing duplicated work.

## Fault Recovery

Execution progress is persisted in the database, allowing interrupted
executions to continue exactly from the last successful page.

## Intelligent Deduplication

Every procurement receives a deterministic hash to guarantee idempotent
ingestion.

## Production Deployment

Runs inside Docker containers behind Nginx with HTTPS and scheduled
automation.

------------------------------------------------------------------------

# Design

-   Hexagonal Architecture
-   Repository Pattern
-   Adapter Pattern
-   Command Pattern
-   SOLID Principles
-   ETL Architecture

------------------------------------------------------------------------

# Documentation

Additional technical documentation is available upon request and covers:

------------------------------------------------------------------------

# Roadmap

-   CI/CD pipeline
-   Monitoring dashboard
-   Metrics visualization
-   Additional data providers
-   AI-assisted procurement classification

------------------------------------------------------------------------

# Disclaimer

This repository is a public showcase.

Some commercial modules and business rules have been intentionally
omitted because they are part of a production commercial system.

------------------------------------------------------------------------

# Author

**Albert Pimentel França**

Backend Python Developer\
Software Engineer

LinkedIn: https://linkedin.com/in/albertpimentel-franca

GitHub: https://github.com/PJKTDELFOS
