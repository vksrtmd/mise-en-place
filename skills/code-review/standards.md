# Smell baseline

Applies on top of whatever the repo documents; skip a smell a documented repo standard endorses or tooling already enforces. Each is a judgement call, labelled "possible X". Match each against the code in scope.

Fowler smells (_Refactoring_, ch.3): Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Message Chains, Middle Man, Refused Bequest, and **Speculative Generality** (an interface with one implementation, a factory with one product, parameters or hooks no caller uses).

Docs and comments:

- **Expanded Term**: docs or comments spell out a term's current form (`web-<tenant>__<region>`) where the repo's `GLOSSARY.md` defines a term for it (`<slug>`). → use the defined term.
- **History Comment**: a comment narrates the code's past rather than its present: marks where code was deleted (`// removed X`), says what it replaced, or cites an issue or PR (`// see #123`, `// fix for PR 45`). → delete it, move the history to the commit message or PR, and point to a document (ADR, README section) when the reason must stay with the code.
- **Narrating Comment**: a comment or docstring translates the code beside it, or its name and signature, into English (`// increment the retry count`, `// loop over the users`) in code only agents read. A script a person runs by hand is exempt: its step comments are for that person. → delete it, or replace it with what the code can't say: the reason, the constraint, the gotcha.

Tests in scope:

- **Implementation-coupled**: the test mocks internal collaborators, calls private methods, asserts on call counts or call order, or verifies through a side channel (querying the database instead of using the interface). The tell: it breaks on a refactor that keeps behavior. → assert through the public interface.
- **Mechanics-named**: the test name describes how the code works (`checkout calls paymentService.process`) rather than a capability. → name the capability (`user can checkout with valid cart`).
- **Hard-wired boundary**: code under test builds its external client inside itself (`new StripeClient(process.env.STRIPE_KEY)`), or one generic fetcher forces the mock to branch on endpoint. → inject the dependency, one function per external operation.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a hand-derived snapshot, a constant asserted equal to itself). → take expected values from a known-good literal, a worked example, or the spec.
