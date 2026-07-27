---
name: lvfi-pricing-engine
description: Guard frozen LVFI Pricing Engine versions, schemas, hashes, Method 1 and validation baselines.
---

# LVFI Pricing Engine

## Use when

Changing `packages/pricing-engine` or when a final validation explicitly requires its gates.

## Do not use when

A task changes only documentation, process, scripts or backend code outside the package.

## Inputs

Approved package scope, version/schema impact and baseline requirements.

## Steps

1. Confirm source contracts, hashes, Method 1, 10×10 scenario and Asian settlement requirements.
2. Do not alter fixtures, expected values, versions or hashes to hide divergence.
3. Run the `pricing` profile and required package gates.

## Success

Frozen mathematics and public artifacts remain demonstrably intact.

## Stop

Stop for incidental package change, baseline divergence, schema/version change outside scope or missing authorization.

## References

Package documentation and tests; `r21-quality-gates`.

## Minimal output

Scope, invariant evidence, gate summary and residual risk.