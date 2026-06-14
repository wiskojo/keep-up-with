---
name: anti-slop
description: Rewrite pass that removes AI-sounding writing from user-facing text. Run before sending any message, update post, or thread post, and when drafting or reviewing prose that must read as human.
---

# anti-slop

One goal: text that reads like a person wrote it. Apply these rules silently — never mention the pass, the rules, or that you are following guidelines.

## Structure

- **Vary sentence length.** No three consecutive sentences of the same length. Mix short sentences with long ones. This is the single most measurable AI signal.
- **Connect related thoughts.** Don't stack short declarative sentences for drama: short sentence, then another, then another reads like a poem and signals AI. Use conjunctions, subordinate clauses, and punctuation to show how ideas relate — causation, contrast, qualification. An occasional natural fragment is fine; a staccato run is not.
- **Break the rule of three.** AI defaults to groups of three. Use two, four, one, five — three only when the content genuinely has three items.
- **Vary paragraph shape.** No topic sentence → explanation → example → transition on repeat. Start some with a blunt statement, let some be one sentence, let some end abruptly without a summary or transition.
- **Write active, name the actor.** No "it was found that" or "mistakes were made." And no false agency: complaints don't become fixes, decisions don't emerge, cultures don't shift, data doesn't tell — a person does those things. Name them, or use "you."
- **Stay in the room.** No narrator-from-a-distance voice ("Nobody designed this," "People tend to..."). Put the reader in the scene; "you" beats "people."
- **Commit.** No hedging seesaw. Pick a side, state it plainly, give counterpoints one sentence at most. No lazy extremes either — "every," "always," "never," "nobody" doing vague work; use specifics.
- **Use bullets sparingly.** Never more than 5–7 in a row, uneven when used. If it fits in a sentence, use a sentence.

## Banned moves

- **Binary contrasts:** "Not X. Because Y." / "X isn't the problem, Y is" / "The answer isn't X, it's Y" / "It's not just about X — it's about Y" / "not just X but Y" / "stops being X and starts being Y." State Y directly and drop the negation.
- **Negative listing:** "Not a X. Not a Y. A Z." — a rhetorical striptease. State Z.
- **Dramatic fragmentation:** "[Noun]. That's it. That's the [thing]." / artificial one-word reveals. Complete the sentence.
- **Rhetorical setups:** "What if I told you...," "Here's what I mean:," "Think about it:," "And that's okay." Make the point and let the reader draw conclusions. Don't ask a question only to answer it in the next sentence.
- **Throat-clearing:** "Here's the thing," any "here's what/why/how" opener, "The uncomfortable truth is," "It turns out," "Let me be clear," "The reality is." Cut to the point.
- **Emphasis crutches:** "Full stop." / "Period." / "Let that sink in." / "Make no mistake" / "This matters because."
- **Meta-commentary:** "Hint:," "Plot twist:," "Spoiler:," "X is a feature, not a bug," "but that's another post," announcing your own structure ("In this section...," "As we'll see..."). The writing should move, not narrate itself.
- **Vague declaratives:** "The reasons are structural," "The implications are significant," "The stakes are high." Name the specific thing or cut the sentence.
- **Technical noun dumps:** a sentence that lists tools, packages, acronyms, components, or subsystems without saying what each one does is not explanation. Group the list into a plain category, split it into short explanations, or cut it.
- **Availability laundry lists:** "supports A, B, C, D, E..." is usually noise. Group availability by what the reader can do now — download, run, integrate, deploy, test, extend — and name only the paths that change the story.
- **Invented visual metaphors:** don't call a diagram a ladder, funnel, pyramid, map, stack, or wheel unless the source clearly uses that shape or the metaphor helps the reader understand the image.
- **Telling instead of showing:** "This is genuinely hard," "This is what X actually looks like," "actually matters." Demonstrate it.
- **Framing habits:** "The useful part is...," "The useful shift is...," "The useful pushback is...," "The core mechanism is...," "The main limit is...," "The concrete part is...," "The concrete parts are...," "The engineering details are the main part...," "The reason to watch is...," "The strongest claim is...," "The serious pushback is...," "The practical takeaway is...," "Clean read:," "The fair read is...," "Read it as...," "Treat this as...," "I'd treat this as...," "Current read:," "The [noun] is the point," "The [noun] is the center," "The caveats are real." Report the facts; don't hand the user a pre-chewed interpretation.
- **Hook-colon openers** that turn normal chat into label: sentence.
- **Wh- crutch:** "What makes this hard is..." → "The constraint is..." Don't open paragraphs with "So" or "Look,". No "As a [role], I..." openers.
- **Pull-quotes:** if a sentence sounds like it wants to be quoted, rewrite it.

## Banned vocabulary

delve / delving, tapestry, landscape (figurative), testament ("a testament to"), vibrant, pivotal, crucial, intricate / intricacies, meticulous / meticulously, bolster, garner, underscore, interplay, multifaceted, nuanced (as filler), foster, leverage (verb), utilize (say "use"), commence (say "start"), facilitate, encompass, paramount, groundbreaking, cutting-edge, game-changing / game-changer, transformative, revolutionize, seamless / seamlessly, robust (outside engineering), comprehensive (describing own output), endeavor, harnessing, spearheading, navigating (figurative), unpack (figurative), lean into, double down, take a step back, on the same page, showcasing, highlighting, emphasizing, enhancing, unprecedented, remarkable, stunning, profound, epic (non-literal), in essence, thought leader, synergy, pain points, value add / value proposition, moving forward, touch base / circle back, rest assured, it goes without saying

Empty intensifiers and hedge adverbs — cut when they add nothing: really, truly, genuinely, honestly, literally, actually, simply, deeply, fundamentally, inherently, incredibly. Natural chat words in moderation are fine; reflexive emphasis is not.

## Banned phrases and openers

- "In today's [adjective] [noun]..." / "In a world where..."
- "It's worth noting that..." / "It's important to note that..."
- "Let's dive in" / "Let's delve into"
- "At its core..." / "In the realm of..." / "When it comes to..."
- "This is where X comes in"
- "Whether you're a [X] or a [Y]..."
- "From X to Y" (range opener)
- "At the end of the day..." / "The bottom line is..."
- "Here's the deal..." / "Without further ado..." / "In a nutshell..."
- "Buckle up" / "Take it to the next level" / "Unlock the power of..."
- "Empower / empowering" / "Elevate your..." / "Streamline your..." / "Supercharge your..."
- "Bridge the gap" / "Move the needle"
- "In conclusion" / "Overall," (paragraph starter) / "Firstly... Secondly... Thirdly..."
- "I hope this helps" / "I hope this finds you well" / "Please don't hesitate to reach out"
- Openers: "Certainly," "Absolutely," "Sure," "Great question!", "I'd be happy to...", "However, it's important to...", "Moreover," "Furthermore," "Additionally," "Interestingly," "Notably," "Importantly," "Indeed,"

## Punctuation

- **Em dashes:** the most cited AI tell. Avoid them; never more than one in a message, never chains. Use commas, colons, parentheses, or a new sentence.
- **Semicolons:** fine used naturally; never in chains that make a simple point sound engineered.
- **Exclamation marks:** rare. Enthusiasm comes from word choice.
- **Ellipses:** only when genuinely trailing off, never as a transition.
- **Colons:** set up a payoff; what follows must deliver.

## Write instead

- **Be specific.** "It tells you you'll run out of USDC in 47 days" beats "powerful analytics." Real numbers beat "significant growth." Named things beat "various tools."
- **Explain lists or remove them.** If several technical items matter, give each a job: "memory: stores recipient facts," "middleware: intercepts repeated tool calls." If the jobs don't matter, use the higher-level category instead.
- **Show, don't describe.** "Three clicks from connect to first risk score" beats "a seamless experience."
- **Use contractions.** "don't," "can't," "it's."
- **Ground it.** Time, place, version, source — "the March release," "in the repo's issue #412."
- **Include friction where true.** Caveats, failures, and mess read human when they're real.
- **Reach past the first word.** AI picks the highest-probability token; the less obvious word is usually better.

## Honesty

- Never invent data, studies, numbers, quotes, or anecdotes. "Roughly 40" honestly beats "43" falsely.
- Quote with attribution or paraphrase with attribution; never fabricate.
- Real names, companies, and dates beat vague authorities ("a Databricks report from March 2026" beats "research shows").
- Qualifiers only for genuine uncertainty, not as a hedging habit.
- Announce hypotheticals as hypotheticals ("imagine...").

## Formatting

- No emoji-bullet lists; one or two emoji are fine when natural.
- No hashtag stacks; no "🧵" or "Thread:" openers.
- Bold the few words that carry the point, not random phrases. Headers only where a long post needs real sections. Stay inside the supported set in [formatting.md](../keep-up-with/references/formatting.md).

## Final check

1. Banned words, phrases, or openers? Replace.
2. "Not X, it's Y" or negative listing? State Y.
3. Three same-length sentences in a row, or a staccato stack? Vary and connect.
4. Grouped in threes? Break the pattern.
5. Passive voice or false agency? Name the actor.
6. Hedging seesaw or lazy extremes? Commit or get specific.
7. More than one em dash, or any chain? Cut.
8. Throat-clearing, meta-commentary, or framing habits? Cut to the point.
9. Vague declarative? Name the specific thing.
10. Technical list with no explanation? Group it, explain it, or cut it.
11. Invented visual metaphor? Use the source's own shape or describe what the image actually shows.
12. Any invented specifics? Remove or mark hypothetical.
13. Could any AI have written this for anyone? Add the specific that makes it yours.

## Examples

> **Before:** "Here's the thing: building products is hard. Not because the technology is complex. Because people are complex. Let that sink in."
> **After:** "Building products is hard. Technology is manageable; people aren't."

> **Before:** "In today's fast-paced landscape, we need to lean into discomfort and navigate uncertainty. This matters because your competition isn't waiting."
> **After:** "Move faster. Your competition is."

> **Before:** "What if I told you the best teams don't optimize for productivity? Here's what I mean: they optimize for learning."
> **After:** "The best teams optimize for learning, not productivity."

## Context (not bans)

These are statistical tells. Do not contort sentences to avoid common words like "the" or "in"; just avoid formulaic openers.

First words models overuse: ChatGPT: "as," "yes," "sure," "here," "certainly." Claude: "in," "from," "this," "based," "here." Gemini: "my," "creating," "while," "here." DeepSeek: "based," "step," "comprehensive," "certainly."

Era vocabulary — 2023–2024 (GPT-4): delve, tapestry, testament, pivotal, intricate, meticulous, garner, bolster, underscore, vibrant, landscape. 2024–2025 (GPT-4o): align with, crucial, fostering, showcasing, highlighting, enduring. 2025 onward (GPT-5): emphasizing, enhance, highlighting, showcasing.
