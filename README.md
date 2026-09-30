# The Unofficial Guide

**Son Nguyen.** Corpus: `city_guides`.

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

I used AI as a support tool throughout the project, mainly to clarify concepts,
review my approach, troubleshoot issues, and suggest possible solutions. I used
these suggestions as a starting point, then reviewed the code, tested the
results, and made adjustments based on my own observations.

**1. Reviewing the RAG implementation**

I asked AI to help me understand parts of the RAG pipeline and check whether my
implementation matched the project requirements. It helped explain concepts such
as chunking, retrieval, source attribution, grounding, and relevance checking.

One suggestion about source attribution did not completely match my
implementation. After reviewing `generate.py` and `app.py`, I confirmed that the
model is instructed to name the source in its answer, while the application
separately displays the retrieved sources. I updated my reasoning to reflect
what the code actually does rather than relying on the initial explanation.

**2. Testing retrieval and the relevance threshold**

I also asked AI for help interpreting retrieval-distance results and thinking
through a reasonable relevance threshold. The initial test results showed a
clear difference between the in-scope and out-of-scope questions, so the first
suggestion was based on that separation.

I tested additional questions myself, including less specific in-scope questions
and travel-related questions outside the corpus. Some of these results overlapped
more than the original test set suggested. Based on the additional testing, I
adjusted my reasoning and selected the final threshold in `config.py` based on
the observed behavior of the retrieval and relevance-gating system.

In a few cases, actual test results were also different from the initial
expectations. For example, the hospital question successfully retrieved
`guide_accessibility.md` as the top result. I used the actual retrieval results
when evaluating the acceptance criteria and making final decisions.

Overall, AI was useful for explaining concepts, troubleshooting, and reviewing
possible approaches. I verified suggestions by inspecting my implementation and
running my own tests, and I made changes when the actual results differed from
the initial suggestions.

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

Raw data: `results/run_2026-09-29_2345_before.md`, produced by
`run_eval.py::main`. 15 model calls with caching off, so these are three real
passes rather than one answer shown three times.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks stand on their own | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 5. Contradictions surfaced, not resolved silently | names >1 source or refuses | yes | yes | yes | MET |

**Why three criteria give identical columns.** Criteria 1, 3 and 4 do not
depend on the generated answer. Retrieval is deterministic, the gate is a
comparison against a fixed number, and `app.py chunks -n 5` samples the same
five chunks every time — I ran it three times to check. One measurement is the
whole measurement for those, and it goes in all three columns.

Criteria 2 and 5 do depend on the model, and the raw output confirms generation
really was varying: the Halden Bay parking answer is worded differently in all
three runs, and the hospital answer reorders its list. What did not vary was
whether a source was named or whether the disagreement was reported — which is
the thing being measured.

**Criterion 1 was measured strictly.** Rather than checking that the right
*file* came back, I checked that the `expects` string itself appears inside one
of the five retrieved chunks:

| Question | expects | Found in |
|---|---|---|
| When does the Kestrelford bakery sell out? | `11am` | `guide_kestrelford.md` |
| How much does it cost to climb the church tower in Kestrelford? | `£2` | `guide_kestrelford.md` |
| How often do the trams run in Marchwood on weekdays? | `8 minutes` | `guide_marchwood.md` |
| What is the parking situation in Halden Bay on a summer weekend? | `10am` | `guide_halden_bay.md` |
| Where is the nearest full hospital in the region? | `Marchwood` | `guide_accessibility.md` |

That is 5 of 5 against a target of 4 of 5. Last unit I predicted the hospital
question would be the one to fail, because nine chunks carry the wrong claim
and one carries the right one. It ranked first anyway, at distance 0.4073.

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

### Real output

All answer text below is from run 1 unless marked otherwise, copied from
`results/run_2026-09-29_2345_before.md`. Answers produced by
`generate.py::answer_from_chunks`; retrieval by `store.py::search` over chunks
from `chunker.py::split_documents`; the gate by `gate.py::check`.

**Criterion 1 — retrieved chunk contains the answer.** The chunk that carried
the answer for the hospital question — `guide_accessibility.md#4`, produced by
`chunker.py::split_documents`, retrieved at distance 0.4073 by
`store.py::search`:

```
Getting around the region with limited mobility — Practical

The nearest full hospital is in Marchwood. Brightwater has a hospital;
Kestrelford, Halden Bay, Corry Vale, Givens Mill and Elder Ness have minor
injuries units with limited hours or nothing at all.

Mobile coverage is good in the town centres and patchy on the outskirts, and
genuinely absent in parts of Corry Vale.
```

**Criterion 2 — every answer names a source.** Two of the five, showing the
citation inside the answer text rather than the separate `Sources retrieved:`
line that `app.py` prints:

```
The Kestrelford bakery sells out by 11am (guide_kestrelford.md).
```

```
It costs £2 to climb the church tower in Kestrelford (guide_kestrelford.md).
```

**Criterion 3 — the gate stops out-of-corpus questions.** Produced by
`run_eval.py::check_out_of_scope` at cutoff 0.75:

```
| What is the capital of Mongolia?                            | 0.808 | refused |
| How do I change the oil in a diesel engine?                 | 0.881 | refused |
| Who won the 1994 World Cup?                                 | 0.982 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.835 | refused |
| How do I write a for loop in Rust?                          | 0.859 | refused |
-> gate refused 5 of 5
```

**Criterion 4 — chunks stand on their own.** The five sampled by
`app.py chunks -n 5`, produced by `chunker.py::split_documents`. Four answer a
question unaided; the first does not:

```
Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

That is the preamble chunk — the text above a guide's first `##` heading. It
tells you a guide exists and nothing more, so I scored it a fail. Compare
`guide_pellew_sands.md#6` from the same sample, which answers "when should I
visit Pellew Sands?" by itself:

```
Pellew Sands — When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

**Criterion 5 — contradictions surfaced.** Run 1 and run 3 of the hospital
question, showing that the wording moved but the behaviour did not:

```
The documents disagree on the location of the nearest full hospital:
- According to `guide_accessibility.md`, the nearest full hospital is in Marchwood.
- According to `guide_halden_bay.md`, `guide_kestrelford.md`, `guide_givens_mill.md`, and `guide_brightwater.md`, the nearest full hospital is in Brightwater.
```

```
The documents disagree on the location of the nearest full hospital:

* `guide_accessibility.md` states that the nearest full hospital is in Marchwood.
* `guide_halden_bay.md`, `guide_kestrelford.md`, `guide_givens_mill.md`, and `guide_brightwater.md` all state that the nearest full hospital is in Brightwater.
```

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunks contain the answer | MET | Target was 4 of 5; got 5 of 5 in all three runs, checked strictly by confirming the `expects` string sits inside a retrieved chunk rather than just that the right file came back. |
| 2 | Every answer names a source | MET | 15 of 15 answers across three runs contain a `guide_*.md` filename in the answer body, not only in the `Sources retrieved:` line that `app.py` prints. Met under the strict reading as well as the loose one — but see the revision. |
| 3 | Gate stops out-of-corpus questions | MET | Target was 4 of 5; the gate refused all five `OUT_OF_SCOPE` questions at distances 0.808–0.982, well clear of the 0.75 cutoff. Met against the set the criterion names — but see the revision. |
| 4 | Chunks stand on their own | MET | Exactly at target, 4 of 5. The preamble chunk `guide_accessibility.md#0` answers nothing on its own and I scored it a fail, as I predicted I would last unit. The other four each answer a question unaided. |
| 5 | Contradictions surfaced | MET | The hospital question named both sides and all five documents in all three runs. Worth stating plainly: it only passes because I changed `GROUNDING_INSTRUCTION` in unit 1 after writing the criterion. Before that change the same question returned a single confident citation. |

**Three of these are more comfortable than they should be, and I want that on
the record before the revisions below.** Criterion 2 cannot fail as written.
Criterion 3 passes against a set of questions that was never going to be hard.
Criterion 4 measures the same five chunks forever. None of those is a result I
earned; they are all artefacts of how I wrote the criterion. The verdicts above
stand as MET because that is what the targets say, and a target I hit does not
get moved. The revisions in `criteria.md` fix the measurement for next time,
and two of the three make the criterion strictly harder.

The one number that genuinely surprised me was criterion 1 at 5 of 5. I
targeted 4 of 5 and named the hospital question as the one I expected to lose,
because nine chunks in my corpus carry the wrong claim and one carries the
right one. It retrieved first at 0.4073. My reasoning was that duplication
would crowd out the correct chunk; what I had not accounted for is that the
correct chunk is *about* hospitals in detail while the nine duplicates mention
one in passing, so it is semantically closer despite being outnumbered.

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

**I missed nothing, and three of my five targets were set low.** Criterion 2
could not fail as written, criterion 3 was measured against questions that were
never near the cutoff, and criterion 4 inspected the same five chunks every
time. I revised all three in `criteria.md` last milestone. Only criterion 1
(5 of 5 against a target of 4) and criterion 5 were genuinely cleared.

Revising criterion 3 turned it into a real miss, and that is what the rest of
this section diagnoses. Revising criterion 4 did not: re-measured as 10 random
chunks against two observable tests, it comes out **9 of 10 (MET)**, with the
single failure being `guide_corry_vale.md#0`, a preamble chunk. That matches
the 11 percent preamble rate I calculated, so the chunker is behaving as
described and there is nothing to diagnose there.

### Criterion 3 (revised) — MISSED, 0 of 6

**Stage: embedding.** Not retrieval, and not the gate, though the gate is where
it becomes visible.

**Mechanism.** The embedding encodes the *shape* of a question far more
strongly than the entities in it, so a question with an unfamiliar proper noun
in a familiar frame lands close to my corpus even though nothing in the corpus
is about it. I tested this by holding the sentence frame fixed and changing
only the place name:

| Question | Best distance | Top result |
|---|---|---|
| what is the best time to visit **Halden Bay**? | 0.2261 | `guide_halden_bay.md` |
| what is the best time to visit **Brightwater**? | 0.3067 | `guide_brightwater.md` |
| what is the best time to visit **Kestrelford**? | 0.3269 | `guide_kestrelford.md` |
| what is the best time to visit **Ouagadougou**? | 0.6058 | `guide_seasons.md` |
| what is the best time to visit **Reykjavik**? | 0.6208 | `guide_seasons.md` |
| what is the best time to visit **Zurich**? | 0.6310 | `guide_halden_bay.md` |
| what is the best time to visit **Tokyo**? | 0.6427 | `guide_halden_bay.md` |

The four foreign cities land in a band of 0.037 — Ouagadougou, which appears
nowhere in any travel guide I own, scores *better* than Tokyo. The place name
is doing almost no work. What sets the floor at roughly 0.62 is the frame
"what is the best time to visit ___", which matches the nine `When to go`
sections my chunker produces. Swapping the name moves the distance by about
0.3; the frame alone already puts the question under my 0.75 cutoff.

Working backwards confirms the failure is before generation. For the Tokyo
question all five retrieved chunks are `When to go` sections — `guide_halden_bay.md`,
`guide_seasons.md` ×2, `guide_brightwater.md`, `guide_elder_ness.md` — and the
word "Tokyo" appears in none of them. So generation was never given anything to
answer from.

**Why the gate cannot catch this.** `gate.py::check` sees a single number and
compares it to a threshold. It has no way to tell "0.64 because the topic
matches" from "0.64 because the sentence shape matches". Questions from
genuinely different domains score 0.859 (Rust) and 0.982 (the World Cup)
because their frames match nothing I have, which is why the original criterion
reported 5 of 5 — it only ever tested frames my corpus has no counterpart for.

**The pattern: this is one problem, not six.** All six travel questions I
measured — Barcelona, Edinburgh, the Louvre, Paris, Tokyo, Heathrow — are the
same failure. Each pairs a question frame my guides answer often (when to
visit, how to get there, where to park, opening hours, is the bus cheaper) with
a proper noun my guides have never heard of. There is no sixth diagnosis to
write; there is one mechanism with six instances.

It is also unfixable by moving the threshold, which is the part I want on the
record. Legitimate vague questions about my own region score 0.609 to 0.722,
and these score 0.575 to 0.643. **They overlap, so no cutoff separates them.**
Lowering the threshold to 0.57 to exclude the Barcelona question would also
refuse "where do locals eat rather than tourists?", which is a question my
corpus answers well. The two layers currently divide the work: the gate stops
questions whose frame is foreign, and `GROUNDING_INSTRUCTION` stops questions
whose frame is familiar but whose subject is absent. I verified in unit 1 that
the second layer refuses all six. That is a real defence, but it is one prompt
instruction away from silently failing, and it costs a model call every time.

### What I would tighten

**Criterion 1**, from "the retrieved chunks include one that contains the
answer" at 4 of 5, to **"the chunk containing the answer is in the top 3"** at
5 of 5. I cleared the original with the answer ranked first on all five
questions, so 4 of 5 anywhere in the top 5 was never going to test anything.

**Criterion 5** is measured on one question asked three times, so it tests one
retrieval result rather than the system's handling of disagreement. I went
looking for a second contradiction to widen it with and mostly did not find
one: the same boilerplate block repeats claims about cash and mobile coverage,
but `guide_accessibility.md` never mentions cash at all, and on coverage it
adds detail ("genuinely absent in parts of Corry Vale") rather than
contradicting. The only clean conflict in the corpus is the hospital.

So the honest tightening is not "more contradictions" but a harder version of
the same one: the two documents that contradict *themselves* —
`guide_brightwater.md` says the nearest full hospital is in Brightwater, and
`guide_marchwood.md`, the town that actually has it, says the same. Asking
"does Marchwood have a hospital?" puts that self-contradiction in front of the
model directly, and I have never run it.

## The Improvement

**What I changed:** One thing. `gate.py` now runs a second test alongside the
distance check: `gate.unknown_proper_nouns` refuses a question that contains a
capitalised word appearing nowhere in the corpus. The four places that call
`gate.check` now pass the question text through so it can see it. Nothing else
moved — same chunker, same embedding, same threshold of 0.75, same top-k,
same grounding prompt.

**Why I picked it:** My diagnosis was that the embedding scores a question by
its frame and almost ignores the entity in it, so the fix checks the entity
directly — which is the one thing distance provably cannot do here, because
legitimate vague questions (0.609–0.722) and off-topic travel questions
(0.575–0.643) overlap.

**Why I did not pick hybrid search,** which was the recommended default and
which I started on first. My diagnosis says the problem is that proper nouns
carry no weight, so BM25 looked like the obvious answer. I measured it before
building it, and it does not separate the groups either:

| Question | BM25 max score |
|---|---|
| How much does it cost to climb the church tower in Kestrelford? | 15.49 |
| **is the bus to Edinburgh cheaper than the train?** | **13.28** |
| What is the parking situation in Halden Bay on a summer weekend? | 13.41 |
| When does the Kestrelford bakery sell out? | 11.04 |
| which places are difficult with a wheelchair? | 7.62 |

The Edinburgh question outscores four of my five real test questions. BM25
gives an unseen term an IDF contribution of zero — it *ignores* "Edinburgh"
rather than penalising it — so the score comes entirely from "bus", "cheaper"
and "train", which are ordinary corpus vocabulary. Adding it would have been
picking a fix because it sounded impressive.

I also tested a middle option, the fraction of a question's content words
present in the corpus. That fails for the same reason in a different costume:
"Tokyo" scores 0.75 coverage and so does "When does the Kestrelford bakery
**sell** out?", because "sell" happens not to appear either. The count of
missing words carries no signal; which word is missing does.

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

Raw data: `results/run_2026-09-30_0023_after.md`, produced by
`run_eval.py::main`. 15 model calls, caching off.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks stand on their own | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 5. Contradictions surfaced | names >1 source or refuses | yes | yes | yes | MET |

### Before and after, side by side

The five criteria as originally written cannot show this change at all —
every one of them was already MET, and all five are still MET. The row that
moves is criterion 3 **as revised in unit 2**, which is the only real miss I
had:

| Criterion | Target | Before | After | Verdict |
|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | MET → MET |
| 2. Every answer names a source (revised: in answer body) | 5 of 5 | 15/15 | 15/15 | MET → MET |
| 3. Gate stops out-of-corpus questions (original set) | 4 of 5 | 5/5 | 5/5 | MET → MET |
| **3r. Gate stops out-of-corpus questions (revised set)** | **4 of 6** | **0/6** | **6/6** | **MISSED → MET** |
| 4. Chunks stand on their own (original fixed sample) | 4 of 5 | 4/5 | 4/5 | MET → MET |
| 4r. Chunks stand on their own (revised: 10 random) | 8 of 10 | 9/10 | 9/10 | MET → MET |
| 5. Contradictions surfaced | >1 source or refuse | 3/3 | 3/3 | MET → MET |

**Did it help? Yes, and I can say how I know.** The six travel questions that
every previous version of this system answered — or rather, passed to the model
and relied on the prompt to decline — are now stopped by the gate, and the
distances show why they could not have been stopped by tuning:

```
REFUSED  0.575  ['Barcelona']       how much does a hotel in Barcelona cost in August?
REFUSED  0.588  ['Edinburgh']       is the bus to Edinburgh cheaper than the train?
REFUSED  0.604  ['Louvre']          what are the opening hours of the Louvre?
REFUSED  0.633  ['Paris', 'Lyon']   how do I get from Paris to Lyon by train?
REFUSED  0.643  ['Tokyo']           what is the best time to visit Tokyo?
REFUSED  0.643  ['Heathrow']        where should I park at Heathrow airport?
-> 6/6
```

Every one of those is *under* the 0.75 cutoff and would still be under any
cutoff that keeps my own questions working. They are refused on the second
test, not the first.

**The check that matters more than the improvement** is that nothing else
broke. The six legitimate vague questions that motivated raising the threshold
to 0.75 in unit 1 all still pass:

```
allowed  0.491  []  what should I know before driving to the coast?
allowed  0.519  []  where can I get fresh bread early in the morning?
allowed  0.552  []  somewhere quiet to go in winter?
allowed  0.609  []  where do locals eat rather than tourists?
allowed  0.639  []  which places are difficult with a wheelchair?
allowed  0.722  []  is it hard to get around without a car?
-> 6/6
```

A refusal filter that refuses more is trivial to build; this one costs nothing
on the questions the corpus can answer, including three that sit above the old
0.6 cutoff.

**What it does not fix.** Two of the five original `OUT_OF_SCOPE` questions —
the diesel engine and the ibuprofen one — contain no proper noun at all, so the
new test is blind to them. They are still refused, but by distance (0.881 and
0.835), exactly as before. The two tests cover different failures and neither
covers both: distance catches a foreign subject, the proper-noun check catches
a familiar frame around an absent entity. A question that is off-topic, has no
capitalised name, and happens to borrow my corpus's phrasing would pass both,
and I have not constructed one to see.

It is also defeated by word order. `unknown_proper_nouns` skips the first word
because sentence position capitalises it, so "Tokyo in November, what is it
like?" slips through. I chose that trade deliberately rather than lowercasing
the first word and losing every question that legitimately opens with a town
name, but it is a real hole and it is in the docstring.

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
