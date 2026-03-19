# Introduction

## What This Project Is

Polymarket Arbitrage Engine is a focused trading infrastructure project for fee-free binary markets on Polymarket.

It is designed around a narrow but practical goal: detect executable `buy-both-and-merge` arbitrage opportunities in real time, size them under capital constraints, reserve capital before execution, and route them through a mock or real execution interface.

Instead of trying to solve every trading problem at once, this project concentrates on the core pipeline that a serious event-driven arbitrage system needs:

- live market discovery
- real-time market data ingestion
- local top-of-book state maintenance
- opportunity filtering
- capital-aware allocation
- execution orchestration

## What It Does Today

At its current stage, the engine can:

- discover live fee-free `Yes/No` markets from the Gamma API
- subscribe to Polymarket market WebSocket streams
- maintain local `YES` and `NO` best bid / best ask state
- detect `buy-both-and-merge` opportunities
- filter weak opportunities by edge, expected net PnL, and ROI
- dynamically switch allocation preference between absolute profit and ROI based on capital utilization
- greedily reserve capital across opportunities in real time
- execute through either a mock executor or a real CLOB executor interface

This makes the project more than a market scanner, but still intentionally short of a full production trading system.

## Why It Matters

Most public trading repositories are either:

- research notebooks without execution logic
- rough scripts without system structure
- large frameworks that are hard to understand or extend

This project aims to sit in the middle:

- concrete enough to run
- structured enough to extend
- narrow enough to reason about

The codebase is meant to be useful for:

- engineers building prediction market trading systems
- researchers studying microstructure inefficiencies in binary markets
- developers who want a clean reference architecture for event-driven execution pipelines

## Current Boundaries

The engine is still deliberately conservative in scope.

It does not yet include:

- merge settlement execution
- full order lifecycle management
- portfolio reconciliation
- persistent storage
- full-depth order book support
- inventory optimization

Those pieces are natural next steps, but they are not hidden behind marketing language here. The project is strongest when presented honestly: it is a serious, well-structured arbitrage engine foundation with real-time data handling, capital allocation logic, and an execution-ready design.

## Short GitHub Intro

If you want a concise GitHub-facing summary, use this:

> A real-time Polymarket arbitrage engine for fee-free binary markets, with top-of-book scanning, capital-aware allocation, and execution-ready architecture.
