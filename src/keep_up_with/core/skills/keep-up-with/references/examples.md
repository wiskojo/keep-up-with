# Examples

These are references for tone and shape, not templates to follow mechanically.

## Good Quick Message

> A new model release landed from an open-weight lab. The useful bit is that the repo includes inference code and eval scripts, not just a PDF. I’m checking the benchmark claims against comparable open models before making a thread.

Why it works: short, factual, no fake verdict, says what matters.

## Good Thread Update

> The release now has three things worth separating:
>
> First, the model card claims a coding jump, but the published evals are mostly saturated benchmarks. I pulled the comparable scores from the last two strong open models so the numbers are easier to read.
>
> Second, the repo has runnable inference code but no training config. That makes it useful to try, not enough to understand how they got the result.
>
> Third, most of the discussion is about deployment size and tokenizer behavior. I linked the two comments that actually add details instead of reposting the launch.

Why it works: it reports, compares, and filters without pretending to know more than the sources support.

## Bad Preambles

Avoid:

> New detail:

> The interesting bit is not...

> I’d treat this as promising but screenshot-driven...

> This is worth watching.

These waste space or narrate internal judgment. State the facts instead.

## Bad Benchmark Note

Avoid:

> The model gets 63 on AIME and 72 on LiveCodeBench.

Better:

> The headline scores are 63 on AIME and 72 on LiveCodeBench. Those are hard to interpret alone because both benchmarks are crowded now. I’m comparing against current frontier and open-weight baselines before treating this as a real jump.

Why it works: the raw numbers get context.
