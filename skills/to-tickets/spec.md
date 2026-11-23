# Spec

Turn the conversation and your codebase understanding into a spec and publish it to the tracker. Synthesize everything else from what you already know; the user's one input is the seam check (step 1).

## Process

1. Sketch the seams at which you'll test the feature. Prefer existing seams to new ones, and the highest seam possible; propose new ones at the highest point you can. The fewer seams the better: the ideal is one.

   Check with the user that these seams match their expectations.

2. Write the spec with the template below and publish it to the tracker. Apply the `ready-for-agent` label; no further triage.

<spec-template>

## Problem Statement

The problem the user is facing, from the user's perspective.

## Solution

The solution, from the user's perspective.

## User Stories

A numbered list covering every aspect of the feature, each as:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

## Implementation Decisions

The decisions made, e.g. modules built or modified, their interfaces, technical clarifications from the developer, architecture, schema changes, API contracts, specific interactions.

Describe decisions in prose; file paths and code snippets go stale. Exception: when a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline the decision-rich part within the relevant decision and note it came from a prototype.

## Testing Decisions

- What makes a good test (only external behavior, not implementation details)
- Which modules will be tested
- Prior art: similar tests in the codebase

## Out of Scope

What is out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
