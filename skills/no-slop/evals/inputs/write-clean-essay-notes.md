# Notes for the essay: why small teams ship faster

Audience: my blog (engineers and founders). Target ~500 words. Don't invent facts or numbers beyond what's here.

## Rio Tanaka quotes (verbatim, use where they hit)

- "A team of four ships like a team of four. A team of forty ships like a committee." — x.com/riotanaka, 2025-02-03
- "Coordination is the tax. Headcount is the rate." — x.com/riotanaka, 2025-04-18

## Material

- Parcelbay (6 people) rebuilt their entire checkout in 11 days after the 40-person incumbent they integrate with quoted "a quarter, maybe two" for the same change.
- The catch: in week 2 Parcelbay also shipped a billing bug that double-charged 41 customers, because nobody reviewed the migration. They refunded same-day and published the postmortem. Small teams cut review, not just meetings. Use this honestly — it's the cost side, not a gotcha.
- My core argument: speed isn't heroics, it's the absence of coordination overhead. Every additional person adds edges to the communication graph, and edges are where weeks go.
- Standups, design reviews, approval chains: each exists to manage mistrust between people who don't share context. Four people share context by osmosis.
