# Current Spyre Software Stack and vllm-spyre-next

Last updated: 2026-03-16

<details markdown="1">
<summary><strong>Purpose</strong></summary>


This document is the umbrella topic for understanding the transition from the
current `vllm_spyre` path to `vllm-spyre-next`.

It is the best starting point when the question is:

- what exactly is changing?
- why are there two stacks at all?
- which parts of the system are stable versus transitional?
- how should work be staged across the transition?

</details>

<details markdown="1">
<summary><strong>Where This Fits</strong></summary>


- Back to the big picture: [../../README.md](../../README.md)
- Topic index: [../README.md](../README.md)
- Neighbor topic: [Execution and Attention](../execution-and-attention/README.md)
- Neighbor topic: [Compiler/Runtime Contracts](../compiler-runtime-contracts/README.md)
- Neighbor topic: [Spyre Device and Inductor](../spyre-device-and-inductor/README.md)
- Neighbor topic: [Validation and Proof Plan](../validation-and-proof-plan/README.md)

</details>

<details markdown="1">
<summary><strong>Engineer Lenses</strong></summary>


### Current `vllm_spyre` engineers

This topic should answer:

- which current seams are intentional versus transitional
- what should keep carrying near-term proof work

### `vllm-spyre-next` engineers

This topic should answer:

- which ownership is supposed to migrate out of the plugin
- what not to assume is already mature

### Upstream vLLM engineers

This topic should answer:

- why Spyre currently carries more custom plugin logic
- what the long-term upstream-shaped target actually is

### `torch-spyre` engineers

This topic should answer:

- which `vllm-spyre-next` goals depend on substrate maturity
- which blockers are genuinely lower-layer blockers versus plugin design choices

</details>

<details markdown="1">
<summary><strong>First Principles</strong></summary>


### Why do the current Spyre software stack and `vllm-spyre-next` both exist?

An accelerator plugin exists to bridge several layers:

- application-level serving behavior
- model execution
- attention / KV representation
- compiler behavior
- runtime / device behavior

If those lower layers are immature or unusual, the plugin tends to absorb more
custom behavior. If those lower layers mature and become more upstream-shaped,
the plugin can become thinner.

That is the core reason there are two actively discussed Spyre stack shapes:

```text
  current Spyre software stack
    -> more custom behavior in the plugin

  vllm-spyre-next / new stack
    -> less custom behavior in the plugin
       and more reliance on upstream vLLM + torch-spyre
```

### What is actually changing?

Not just one thing. Several transitions are happening at once:

- FMS model code -> upstream vLLM model code
- custom execution path -> more upstream-shaped execution path
- worker/model-runner-centric integration -> thinner plugin integration
- current runtime/compiler contracts -> torch-spyre-centric contracts

Those are related transitions, but they are not identical transitions.

</details>

## Generic Transition Model

```text
                 ONE SERVING SURFACE, TWO STACK SHAPES

  user / API / serving request
              |
              v
         upstream vLLM engine
              |
      +-------+--------+
      |                |
      v                v
  current vllm-spyre path      vllm-spyre-next
  more plugin behavior         thinner plugin behavior
  custom execution             upstream-shaped execution
```

## Current Spyre Software Stack

The current Spyre software stack is roughly:

```text
  user / API / LLM.generate
            |
            v
     upstream vLLM engine
            |
            v
       vllm_spyre
       - custom platform
       - custom scheduler
       - custom worker
       - custom model runner
            |
            v
      FMS model code
      FMS attention / KV
            |
            v
     sendnn / current runtime
            |
            v
           AIU
```

### What is good about the current Spyre software stack?

- it is real and working
- it already exposes practical AIU seams
- it is the first place where KV reuse/offload can be proven on hardware

### What is expensive about the current Spyre software stack?

- large plugin surface
- dependence on FMS model code
- custom scheduler/worker/model-runner behavior
- awkward seams for future upstream-aligned features

## vllm-spyre-next / New Stack

`vllm-spyre-next` is roughly:

```text
  user / API / LLM.generate
            |
            v
     upstream vLLM engine
            |
            v
     vllm-spyre-next
     - thinner plugin
            |
            v
   upstream model code + Spyre attention backend
            |
            v
      torch-spyre substrate
            |
            v
           AIU
```

### What is good about `vllm-spyre-next`?

- less plugin-specific code
- better alignment with upstream vLLM execution
- better long-term home for offload, disaggregation, and scale-out

### What is not settled yet?

- execution maturity
- paged attention maturity
- runtime/copy/stream maturity
- distributed / multi-Spyre maturity

## Transition Tracks

```text
                     STACK TRANSITION TRACKS

  Track 1: plugin surface
    current: custom platform/scheduler/worker/model-runner
    target : thinner plugin with less custom execution logic

  Track 2: model execution
    current: FMS model code + FMS attention
    target : upstream vLLM model code + Spyre backend

  Track 3: KV / connector-family features
    current: practical proof seam on the current `vllm_spyre` path
    target : cleaner long-term destination on `vllm-spyre-next`

  Track 4: compiler/runtime contracts
    current: existing runtime/compiler contracts
    target : torch-spyre-centered compiler/backend direction
```

## What Should Stay Stable Through the Transition?

```text
  serving surface
  request semantics
  correctness expectations
  benchmark discipline
  terminology for reuse/offload/disaggregation
```

## What Should Change Over Time?

```text
  execution ownership
  attention backend ownership
  plugin size
  runtime/compiler assumptions
  distributed and topology assumptions
```

## Current Direction

The practical transition strategy today is:

- keep using the current `vllm_spyre` path for the first serious AIU proofs
- keep moving `vllm-spyre-next` forward, but do not overload it too early
- use proof results from the current path to inform the long-term
  `vllm-spyre-next`
  design

That staging looks like:

```text
  current vllm-spyre path proves value now
      ->
  vllm-spyre-next matures underneath
      ->
  the new stack becomes the better long-term destination
```

## Communication Goal

The main communication job of this topic is to help different teams talk about
the transition without collapsing several separate changes into one vague
"migration." It should keep stack transition, execution transition, and
compiler/runtime transition related but distinct.

## Related Source-Repos and References

- `vllm-spyre-next` rationale:
  [vllm-spyre issue #639](https://github.com/vllm-project/vllm-spyre/issues/639)
- `vllm-spyre-next` dev/test readiness:
  [vllm-spyre issue #761](https://github.com/vllm-project/vllm-spyre/issues/761)
- Side-by-side image for the current and new paths:
  [vllm-spyre issue #664](https://github.com/vllm-project/vllm-spyre/issues/664)
- Upstream model-code transition milestone:
  [vllm-spyre issue #666](https://github.com/vllm-project/vllm-spyre/issues/666)
