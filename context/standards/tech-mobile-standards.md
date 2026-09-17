---
purpose: Mobile platform tech stack, tooling, and coding patterns
audience: Mobile developers and agents
read-when: Mobile development, iOS/Android setup
not-for: Web frontend (see tech-standards.md), backend services (see tech-standards.md)
related: [tech-standards, coding-standards, testing-standards]
---

# Mobile Technology Standards

**Status**: Deferred — no active mobile development. Retained for reference when mobile work resumes.

For shared patterns (auth, secrets, monitoring principles), see [tech-standards.md](tech-standards.md).

---

## iOS Platform

```yaml
languages: Swift
architecture: MVVM with SwiftUI
deployment: App Store
testing_targets:
  primary_device: iPhone 16
  primary_os: iOS 18.1
  supported_os_range: iOS 17.0+
```

---

## Android Platform (Future)

```yaml
languages: Kotlin (planned)
deployment: Play Store (future)
```

---

## Build Tools

- **Swift**: Xcode, Swift Package Manager
- **Linting**: SwiftLint
- **Formatting**: SwiftFormat
- Run via root pre-commit or SPM plugins so versions are locked across the team.

---

## Testing

- **Unit**: XCTest
- **UI**: XCUITest

For testing methodology and coverage thresholds, see [testing-standards.md](testing-standards.md).

---

## Monitoring & Error Tracking

- **Analytics**: Firebase Analytics
- **Crash reporting**: Firebase Crashlytics (crash dumps, stack traces, device context)

---

## Optimisation

- Platform-specific builds (single architecture)
- Asset optimisation (compressed images, WebP)
- Offline-first design where applicable

---

## Feature Flags

| Phase | Tool | Usage |
|-------|------|-------|
| Prototype/Dev | Environment variables | Simple on/off |
| Pre-deployment | Firebase Remote Config | `RemoteConfig.remoteConfig()["feature"].boolValue` |

---

## SwiftUI/iOS Coding Patterns

**Architecture:** MVVM with SwiftUI. Prefer structs over classes.

**Structure:** Features/, Core/, UI/, Resources/

**Naming:** camelCase vars/funcs, PascalCase types, Boolean: is/has/should prefix

**Patterns:**

| Area | Use |
|------|-----|
| Concurrency | async/await |
| State | @Published, @StateObject |
| Errors | Result type |
| UI | SwiftUI first, UIKit when needed |
| Icons | SF Symbols |

**Quality:**
- Profile with Instruments
- XCTest + XCUITest
- Support dark mode, dynamic type
- Keychain for secrets, certificate pinning

---

## React Native for Web

**Goal:** Write Once, Run on Multiple Platforms

**Principles:**

1. **Organise Repository for Shared Code**
   - Shared components in `packages/shared-ui/`
   - Platform-specific overrides in `mobile/` and `web/`

2. **Reuse Components Across Platforms**
   - Use React Native primitives (View, Text, etc.)
   - Platform-specific files: `.ios.tsx`, `.android.tsx`, `.web.tsx`

3. **Consolidate State Management**
   - Shared state store
   - Platform-agnostic business logic

4. **Optimise Build and Deployment**
   - Separate build pipelines
   - Shared TypeScript config base

5. **Focus on Developer Experience**
   - Fast refresh for all platforms
   - Shared dev tools and debugging
