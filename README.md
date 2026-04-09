# MACE — Multi-Agent Coordination Engine

## Project Summary

MACE (Multi-Agent Coordination Engine) is a prototype multi-agent orchestration system that coordinates specialized AI agents through a central Orchestrator. The Orchestrator handles task planning, conflict detection, shared state management, and resolution — enabling multiple agents to collaborate on complex user requests without stepping on each other.

## Problem Statement

Modern AI systems increasingly rely on multiple specialized agents to handle diverse tasks. However, when multiple agents operate in parallel, critical coordination challenges arise:

- **Duplicate work** — Independent agents may process the same user intent redundantly, wasting resources and producing conflicting outputs.
- **Conflicting actions** — Two or more agents may attempt to modify the same shared resource (e.g., a support ticket, a database record) simultaneously, leading to data corruption or inconsistent state.
- **Lack of sequencing** — Some tasks have natural dependencies (Agent B needs Agent A's output), but without coordination, agents execute in isolation with no awareness of each other's progress.
- **No shared context** — Agents operating without a common memory layer cannot leverage each other's findings, leading to fragmented and suboptimal responses.

There is a need for a lightweight orchestration layer that sits between the user and the agents — one that can parse intent, route subtasks intelligently, detect and resolve conflicts, and maintain a shared memory so agents work as a coordinated unit rather than isolated silos.

**MACE addresses this by building a centralized orchestrator that manages the full lifecycle of multi-agent task execution — from intent decomposition to conflict-free completion.**

## Objectives

- Build a central orchestrator that decomposes user intent into routable subtasks
- Coordinate two specialized agents (Support Agent + a pluggable Domain Agent) through a shared message bus
- Implement conflict detection when multiple agents act on the same resource
- Provide at least one conflict resolution strategy (rule-based or LLM-based arbitration)
- Maintain a shared memory layer for task state and semantic deduplication
- Demonstrate coordination through three concrete scenarios:
  1. **Duplicate Intent** — Orchestrator deduplicates similar user queries
  2. **Conflicting Update** — Orchestrator arbitrates when agents modify the same resource
  3. **Sequential Dependency** — Orchestrator chains agent outputs where one feeds into the next

## High-Level Architecture

```
User Input
    │
    ▼
┌─────────────────────────────┐
│        Orchestrator         │
│  - Intent Parser            │
│  - Task Router              │
│  - Conflict Detector        │
│  - Arbitration Engine       │
└──────┬──────────────┬───────┘
       │              │
       ▼              ▼
┌────────────┐  ┌──────────────────┐
│  Support   │  │  Custom Domain   │
│  Agent     │  │  Agent           │
└────────────┘  └──────────────────┘
       │              │
       └──────┬───────┘
              ▼
    ┌──────────────────┐
    │   Shared Memory  │
    └──────────────────┘
```

### System Components

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   Orchestrator                      │
│                                                     │
│  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Intent       │→ │   Task     │→ │ Conflict   │  │
│  │ Parser       │  │   Router   │  │ Detector   │  │
│  └──────────────┘  └────────────┘  └─────┬──────┘  │
│                                          │         │
│                                    ┌─────▼──────┐  │
│                                    │ Arbitration│  │
│                                    │ Engine     │  │
│                                    └────────────┘  │
└──────────┬──────────────────┬──────────────────────┘
           │                  │
     ┌─────▼──────┐    ┌─────▼────────────┐
     │  Support   │    │  Custom Domain   │
     │  Agent     │    │  Agent (TBD)     │
     │            │    │                  │
     │ • Tickets  │    │ • Domain-specific│
     │ • FAQs     │    │   tasks          │
     │ • Escalate │    │ • Pluggable      │
     └─────┬──────┘    └─────┬────────────┘
           │                  │
           └────────┬─────────┘
                    │
          ┌─────────▼─────────┐
          │   Shared Memory   │
          │                   │
          │ • Task Registry   │
          │ • Agent Status    │
          │ • Conflict Log    │
          │ • Completed Actions│
          │ • Intent Store    │
          └───────────────────┘
```

## Scope

### In Scope
- Central orchestrator with intent parsing, routing, conflict detection, and resolution
- Two functional agents (Support/Helpdesk + pluggable Domain Agent)
- Shared memory layer for task tracking and deduplication
- Three demo scenarios showcasing coordination capabilities
- Logging and observability of orchestrator decisions

### Out of Scope
- Real-time streaming / webhooks
- Authentication / multi-user sessions
- More than two specialized agents
- Production deployment / containerization / cloud infrastructure

## Tech Stack

*To be decided.* Evaluation in progress — final choices will be documented here once confirmed.

## Team

| Name |
|------|
| Akash Manilal Agarwal |
| Arpit Anil Jaiswal |
| Girish Subhash Nalawade |
| Anmol Sudhir Monde |

## License

TBD
