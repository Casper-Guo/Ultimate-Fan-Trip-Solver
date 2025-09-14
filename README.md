# Ultimate-Fan-Trip-Solver
Say you want to watch your team play every other team in the league...

## Inspiration
Under the current season structure, each NBA, NHL, and MLB team play in every stadium every season, making an ultimate road trip where one travel to see their team play against every away opponent once possible. This trip can be optimized according to a variety of criteria, including total length in days and total distance driven etc.

Similar road trips can be constructed for MLS and NFL (with the caveat of not playing all other teams in the league). Although these trips have less potential for optimization as both leagues play roughly one day a week.

## Generic Problem Formulation
Given a set of events $E = \{E_1, ..., E_n\}$, a cost matrix $C_{n \times n}$ where $C_{ij}$ is a measure of the cost to travel from event $E_i$ to event $E_j$ ($C_{ij} = \infty$ if it is not feasible to attend both $E_i$ and $E_j$), and a decision function $f: e \in \mathcal{P}(E) \mapsto \{\text{yes}, \text{no}\}$, find the open/closed walk through all the events in any set $e \in \mathcal{P}(E), f(e) = \text{yes}$ that minimizes the total cost according to $C$.

The traditional TSP in this formulation uses a decision function $f$ that returns yes if and only if $e = E$ and requires the walk to be closed.
