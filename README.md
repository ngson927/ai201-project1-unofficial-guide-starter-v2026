# The Unofficial Guide

**TODO — PUT YOUR NAME HERE BEFORE SUBMITTING.** Corpus: `city_guides`.

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

This is a question-answering system over `city_guides`, a set of 14 travel
guides for an invented region — nine towns plus five guides that cut across
them on transport, eating, walking, seasons and accessibility. You ask it
something in plain English, it finds the passages most likely to contain the
answer, and it answers from those passages while naming the file each fact
came from.

It handles specific questions well: when the Kestrelford bakery sells out, how
often Marchwood's trams run, what parking in Halden Bay is like on a summer
weekend. It also handles the case where the guides contradict each other —
nine of the fourteen carry a copy-pasted note saying the nearest hospital is in
Brightwater, which is wrong, and the system reports the disagreement rather
than picking a side. When a question falls outside the guides entirely, a
relevance check stops it before it reaches the model and it says so instead of
inventing an answer.

## Chunking Strategy

**Chunk size:** no fixed size — one chunk per `##` section, with `CHUNK_SIZE`
(800) acting as a ceiling rather than a window. Result: 94 chunks, 318
characters on average, shortest 172, longest 758.
**Overlap:** none. `CHUNK_OVERLAP` is still used by `fallback_split` but my
chunker ignores it.

The corpus is 14 long guides already carved into labelled sections — "Getting
there", "Eat and drink", "When to go". I counted 98 of these sections: median
284 characters, 90th percentile 440, longest 711. **Every one of them already
fit inside the starter's 800-character window.** So the fixed-window chunker
wasn't splitting because sections were too big. It was splitting blindly, at
offsets that had nothing to do with the document, and cutting through
boundaries that were already there. Measured on the baseline: 35 of 51 chunks
started mid-sentence, 42 of 51 held pieces of two or more unrelated sections,
and the shortest chunk was 24 characters — `'d Sundays and after 5pm.'`

Splitting at the headings instead takes mid-sentence starts to 0 of 94 and
multi-section chunks to 0 of 94. Overlap then stops earning its keep: overlap
exists to soften the damage when a fixed window severs a thought at an
arbitrary point, and if you split on real boundaries there is no arbitrary
point to soften.

The change that mattered more than the size, though, was context. A section
body almost never names its own town — six of the seven sections in
`guide_kestrelford.md` never contain the word "Kestrelford". The chunk holding
the bakery fact had nothing in it for "when does the Kestrelford bakery sell
out?" to match on. So every chunk is prefixed with its document title and
heading (`Kestrelford — Eat and drink`), which puts the town and the topic into
the text that actually gets embedded. All 8 Kestrelford chunks now name the
town; that question now retrieves the right chunk at distance 0.416 and
answers correctly.

Two things I did not fix. Sections shorter than 120 characters are merged
forward into the next one, because a bare heading with nothing under it is not
worth retrieving — but that threshold is a guess from the size distribution
(the smallest real section is 174 characters), not something I tested. And the
9 documents that repeat the same "Practical notes" boilerplate still produce 9
near-identical chunks, one of which contradicts `guide_accessibility.md` about
where the nearest hospital is. Chunking can't fix that; it's a corpus problem,
and it's what I expect to fail in unit 2.

<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it — the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

This is the weakest of the five and I'm keeping it in rather than cherry-picking
around it. It's a document preamble, so it has a title but no `##` heading, and
on its own it answers nothing — it tells you a guide exists, not what's in it.
Every other chunk in the corpus is a real section.

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
Corry Vale — Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

Answers "where can I stay in Corry Vale?" on its own, including the number of
beds and the camping rule.

**Chunk 3** — source: `guide_givens_mill.md#2` — produced by: `chunker.py::split_documents`

```
Givens Mill — Getting around

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

Without the prefix this would be three sentences about an unnamed village. The
body never says "Givens Mill".

**Chunk 4** — source: `guide_kestrelford.md#4` — produced by: `chunker.py::split_documents`

```
Kestrelford — What to see

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

Three distinct facts with hard numbers — £2, six miles, the 1400s — and it can
answer a question about any of them alone.

**Chunk 5** — source: `guide_pellew_sands.md#6` — produced by: `chunker.py::split_documents`

```
Pellew Sands — When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

Answers "when should I visit Pellew Sands?" completely, and the prefix is what
distinguishes it from the eight other "When to go" sections in the corpus.

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** Where is the nearest full hospital in the region?

**Answer:**

```
The documents disagree with each other regarding the location of the nearest
full hospital:

* guide_accessibility.md states that the nearest full hospital is in Marchwood.
* guide_halden_bay.md, guide_kestrelford.md, guide_givens_mill.md, and
  guide_brightwater.md all state that the nearest full hospital is in
  Brightwater.
```

I picked this one rather than a clean answer because it is the question my
corpus handles worst, and because the first version of it was wrong in a way
that looked right. Before I tightened the grounding instruction, the same
question returned:

```
The nearest full hospital is in Marchwood (guide_accessibility.md).
```

That answer is correct. It is also the answer I most wanted to catch. Four of
the five chunks the model was given say Brightwater; it silently picked the one
that did not and presented it as settled with a single citation. It was right
because `guide_accessibility.md` happened to rank first, not because anything
in the pipeline noticed the disagreement — and if the ranking had gone the
other way it would have said Brightwater with exactly the same confidence.

So I added a fourth rule to `GROUNDING_INSTRUCTION`: if the documents disagree,
say so and name every document on each side, rather than quietly picking one.
That is what produced the answer above. Re-running the other four test
questions and two off-topic ones afterwards showed no change in their
behaviour.

**My relevance cutoff:** `THRESHOLD = 0.75` (raised from the starter's 0.6).

**Top-k:** left at 5. All five test questions find their answer at rank 1, so
retrieval would survive a smaller k — but the hospital question is the reason
not to shrink it. At k=5 the model sees one chunk saying Marchwood and four
saying Brightwater, which is what lets it report the disagreement at all. A
smaller k would hide the conflict rather than resolve it.

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
| How often do the trams run in Marchwood on weekdays? | yes | 0.2189 |
| What is the parking situation in Halden Bay on a summer weekend? | yes | 0.2648 |
| How much does it cost to climb the church tower in Kestrelford? | yes | 0.4059 |
| Where is the nearest full hospital in the region? | yes | 0.4073 |
| When does the Kestrelford bakery sell out? | yes | 0.4161 |
| What is the capital of Mongolia? | no | 0.8084 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8351 |
| How do I write a for loop in Rust? | no | 0.8589 |
| How do I change the oil in a diesel engine? | no | 0.8809 |
| Who won the 1994 World Cup? | no | 0.9819 |

Those ten rows show a gap so wide it is almost useless: 0.4161 to 0.8084, with
nothing in between. Anywhere in that range satisfies criterion 3, and the
starter's 0.6 sits comfortably inside it. If I had stopped here I would have
kept 0.6 and learned nothing.

The gap is that wide because all five `OUT_OF_SCOPE` questions come from
completely different worlds — Mongolia, diesel engines, the World Cup. My five
test questions are also easy: every one names a town or a specific thing, and
none scored worse than 0.4161. Two unrepresentative groups produce a clean
separation that will not survive contact with a real user.

So I measured two more groups the milestone does not ask for.

**Vaguer questions my documents do cover:**

| Question | Best distance | Top result |
|---|---|---|
| what should I know before driving to the coast? | 0.4906 | `guide_halden_bay.md` |
| where can I get fresh bread early in the morning? | 0.5189 | `guide_eating.md` |
| somewhere quiet to go in winter? | 0.5523 | `guide_halden_bay.md` |
| where do locals eat rather than tourists? | 0.6090 | `guide_eating.md` |
| which places are difficult with a wheelchair? | 0.6394 | `guide_accessibility.md` |
| is it hard to get around without a car? | 0.7219 | `guide_halden_bay.md` |

Three of those sit above 0.6, and the top result for each is the right
document — `guide_accessibility.md` for the wheelchair question is exactly
where that answer lives. At the starter's cutoff all three are refused outright
despite retrieval having done its job perfectly. That is the "too low" failure
in the milestone's table, and it is invisible: the user sees a refusal and
assumes the corpus has nothing.

**Questions my documents don't cover, in the same vocabulary:**

| Question | Best distance |
|---|---|
| how much does a hotel in Barcelona cost in August? | 0.5753 |
| is the bus to Edinburgh cheaper than the train? | 0.5881 |
| what are the opening hours of the Louvre? | 0.6035 |
| how do I get from Paris to Lyon by train? | 0.6334 |
| what is the best time to visit Tokyo? | 0.6427 |
| where should I park at Heathrow airport? | 0.6432 |

This is the finding that actually decided the number. These six **overlap
completely** with the legitimate questions above. "is the bus to Edinburgh
cheaper than the train?" (0.5881, should be refused) is *closer* than "where do
locals eat rather than tourists?" (0.6090, should be answered). No threshold
anywhere separates them. The gate cannot tell a travel question about my region
from a travel question about somewhere else, because at the embedding level
they are the same question.

Given that, I picked 0.75 on an asymmetry rather than on a gap. **A wrong
refusal is unrecoverable** — the gate fires before generation, the model never
sees the chunks, and there is no second chance. **A wrong acceptance still has
a second layer**, and I tested that it works: with the cutoff at 0.75 all six
of those travel questions pass the gate, and the grounding instruction refuses
every one of them anyway ("the provided documents do not mention Tokyo"). So
the cost of admitting them is a wasted API call, while the cost of refusing the
wheelchair question is a user who is told, wrongly, that the answer isn't
there.

**What I get wrong at 0.75.** Every one of those six travel questions reaches
the model instead of being stopped by the gate, so I am paying six unnecessary
calls to avoid three wrong refusals, and I am relying on the prompt to hold the
line where the gate cannot. If the model ever stops refusing them, nothing else
catches it. 0.75 also leaves only 0.058 of margin below the nearest
out-of-scope question (0.8084), so criterion 3 passes 5 of 5 but not by much —
one off-topic question phrased in regional-travel language would likely get
through the gate.

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**Scope first, since it affects how the rest of this should be read.** I used
Claude heavily on this project — it wrote the chunker, the five test questions,
the reasons under the acceptance criteria, and most of this README. I chose the
corpus, and I chose the targets for criteria 4 and 5 from options it laid out.
Both moments below are cases where what came back was wrong and had to be
changed, which is the part I want on the record, but I am not going to describe
this as light-touch assistance when it wasn't.

**1. It stated something about my own code that turned out to be false.**

While writing the reason under criterion 2 ("every answer names at least one
source document"), I asked why five of five was a fair target rather than four.
Claude's answer was that source attribution is appended by `generate.py` from a
template, so a miss would mean the code was broken rather than the model
misbehaving. That is a clean justification and I nearly kept it.

It is also wrong. `generate.py` has no such template. `build_prompt` ends with
the instruction "name the file you used", so the citation inside an answer is
written by the model and can be omitted. The only thing my code generates is
the separate `Sources retrieved:` line that `app.py` prints. I rewrote the
reason to say that, and it exposed a real defect in the criterion: read
literally, the sentence counts the code-printed line, which is always there, so
the criterion cannot fail. The fix is three words — "in the answer text
itself" — and I have left it unfixed on purpose so the original stands for
unit 2.

**2. It accepted a clean result that was clean for the wrong reason.**

Milestone 4 asks for the best distance on five in-corpus questions and five
out-of-scope ones, and mine separated perfectly: 0.4161 to 0.8084 with nothing
in between. Claude's first read was that 0.6 sits inside the gap and is fine.

I pushed on why the gap was so wide, and the answer was that both groups are
unrepresentative — the `OUT_OF_SCOPE` questions are about Mongolia and diesel
engines, and my five test questions all name a town outright. So we measured
two groups the milestone does not ask for: vaguer questions the guides do cover,
and travel questions about places they don't. Those two overlap completely,
0.575 to 0.643 against 0.609 to 0.722. "is the bus to Edinburgh cheaper than
the train?" scores closer than "where do locals eat rather than tourists?"

That killed the original reasoning. There is no gap to put a number in, so
0.75 is chosen on an asymmetry instead — a wrong refusal is unrecoverable
because the gate runs before generation, while a wrong acceptance still meets
the grounding instruction, which I tested and which refuses all six travel
questions anyway. The number in `config.py` came out of that second round of
testing, not the first.

**Also worth recording: two of its predictions were wrong.** It wrote in
`criteria.md` that the hospital question would fail retrieval, because nine
chunks carry the wrong claim and one carries the right one. When I ran it,
`guide_accessibility.md` came back ranked first and criterion 1 passed five of
five rather than the four I had targeted. The prediction was wrong, but
criterion 5 caught a subtler version of the same problem anyway — see **Sample
Answer** above.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
