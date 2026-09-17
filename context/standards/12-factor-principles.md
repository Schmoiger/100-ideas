---
purpose: 12-factor app principles for SaaS/service design
audience: Architects, backend developers
read-when: Designing services, evaluating architecture decisions
not-for: Frontend-specific patterns, mobile development
related: [tech-standards, LESS-Engineering-Principles]
---

# 12-Factor App Principles

Reference principles for building software-as-a-service applications with portability and resilience. Originally described at [12factor.net](https://12factor.net/).

1. **Codebase**: Exactly one codebase for a deployed service, used for many deployments
2. **Dependencies**: All dependencies declared, no implicit reliance on system tools
3. **Config**: Configuration that varies between deployments stored in environment
4. **Backing services**: All backing services treated as attached resources
5. **Build, release, run**: Strict delivery pipeline of build → release → run
6. **Processes**: Deploy as stateless processes, persist data in backing services
7. **Port binding**: Self-contained services available via specified ports
8. **Concurrency**: Scale by individual processes
9. **Disposability**: Fast startup and shutdown for robust systems
10. **Dev/Prod parity**: All environments as similar as possible
11. **Logs**: Produce logs as event streams, let execution environment aggregate
12. **Admin Processes**: Admin tasks in source control, packaged with application
