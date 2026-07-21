# TKAI Core Architecture

Version: 1.0.0

Status: Draft

---

# 1. Purpose

The Core module is the foundation of TKAI.

Every subsystem must communicate through Core instead of directly depending on each other.

This keeps the architecture modular, maintainable and extensible.

---

# 2. Architecture

```
                CLI

                 │

                 ▼

              Core Layer

    ┌─────────────────────────┐
    │ Context                 │
    │ Registry                │
    │ Settings                │
    │ Workspace               │
    │ Project                 │
    │ Lifecycle               │
    │ Exceptions              │
    └─────────────────────────┘

                 │

                 ▼

   Template Engine
   Generator
   Plugins
   Workflow
   AI Provider

                 │

                 ▼

            User Project
```

---

# 3. Responsibilities

## Context

Runtime global context.

Responsible for:

- current workspace
- current project
- configuration
- loaded plugins
- runtime state

---

## Project

Represents a TKAI project.

Contains:

- project name
- project path
- template
- metadata
- creation time

---

## Workspace

Represents a workspace.

Responsible for:

- workspace discovery
- workspace root
- project list
- cache directory

---

## Registry

Global registry.

Responsible for registering:

- generators
- plugins
- templates
- AI providers
- workflows

---

## Settings

Core runtime settings.

Responsible for:

- environment
- debug mode
- log level
- cache options

---

## Lifecycle

Application lifecycle.

Stages:

1. initialize

2. load config

3. load plugins

4. register services

5. start

6. shutdown

---

## Exceptions

Unified exception system.

Base class:

TKAIError

Derived exceptions include:

- ConfigError

- TemplateError

- GeneratorError

- PluginError

- WorkflowError

- AIProviderError

---

# 4. Dependency Rules

Allowed:

CLI

↓

Core

↓

Generator

↓

Template

↓

Plugin

↓

Workflow

↓

AI

Not Allowed:

Plugin

↓

Generator

Generator

↓

CLI

Template

↓

CLI

Commands

↓

Generator

Commands should always communicate through Core.

---

# 5. Design Principles

Single Responsibility

Every module has only one responsibility.

Open / Closed

Modules should be extensible without modification.

Dependency Inversion

High-level modules should not depend on low-level modules.

Composition over Inheritance

Prefer composition whenever possible.

---

# 6. Coding Rules

Python >= 3.14

Full type hints

Google style docstrings

pytest coverage required

No circular imports

No global mutable state

---

# 7. Future Extensions

Planned modules:

AI Agent

Workflow Engine

Package Manager

Cloud Deploy

Marketplace

Multi Workspace

Remote Plugin Repository

---

End of Document