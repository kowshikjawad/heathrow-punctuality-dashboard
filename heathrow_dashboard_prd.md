PRD: UK Airport Punctuality Dashboard (Heathrow Focus)
Author: Jawad Bin Sayed | Version 1.0 | 21 October 2026 | Status: Draft
1. Overview
This is a personal portfolio project that turns the UK Civil Aviation Authority's (CAA) public monthly punctuality statistics into a decision-support dashboard. The product is a data pipeline plus a dashboard that shows how Heathrow performs on punctuality, how that compares with other major UK airports, and where delays concentrate by airline and route.
It is built on public CAA data only. It is not affiliated with Heathrow and uses no Heathrow internal data. The user personas below are assumed, not real.
2. Problem statement
Punctuality data is published as monthly spreadsheets and PDFs. They are accurate enough to be useful, but hard to use for fast operational questions: how is performance trending, who is driving delay, and how do we compare with peers? An operations manager should not have to open twelve files to answer those questions.
3. Goals and non-goals
Goals
• Give a single, trustworthy view of Heathrow punctuality over time (target: at least 12 months of data).
• Benchmark Heathrow against peer UK airports on the same measures.
• Let users drill down by airline, route and arrival versus departure.
• Make data quality visible, so users know when to trust a number.
• Provide clear, documented KPI definitions that a non-technical colleague can read.
Non-goals
• Real-time or live flight data.
• Any Heathrow internal or non-public data.
• Predicting delays or modelling root causes (the data does not explain why delays happen).
• A production system. This is a portfolio-quality build.
4. Users and personas (assumed)
Primary: Operations Duty Manager. Needs a quick monthly read on whether performance is improving or slipping, and where to look first. Not a data specialist. Wants answers in under a minute.
Secondary: Performance Analyst. Needs to filter, compare and export, and needs confidence in the numbers and the definitions behind them.
5. Key questions the product must answer
1. How has Heathrow's on-time performance changed month by month?
2. How does Heathrow compare with other major UK airports?
3. Which airlines and routes contribute most to delay and cancellations?
4. Do arrivals and departures behave differently?
5. Can I trust this month's figures, and what changed in the data?
6. User stories
• As a duty manager, I want a one-screen summary of this month's on-time rate, average delay and cancellation rate against last month and last year, so I can see at a glance if we are on track.
• As a duty manager, I want to see which airlines and routes have the biggest delays, so I know where to focus attention.
• As a performance analyst, I want to compare Heathrow with named peer airports on the same measures, so I can put our performance in context.
• As a performance analyst, I want to filter by month range, airline and arrival or departure, so I can investigate a specific pattern.
• As any user, I want to see data-quality checks and known issues, so I know how far to rely on each figure.
7. Data
Source: UK CAA punctuality statistics, published monthly as CSV and PDF files, covering selected UK airports including Heathrow. Files include full analysis and summary analysis, with arrival and departure splits.
Attribution and licensing: the CAA asks that any publication using its statistics references the CAA, and does not permit the data to be sold on. The README and dashboard footer must credit the CAA, and the project must remain non-commercial.
Fields: flight counts, cancellations, delay-band shares and average delay by airport, airline and route. Exact column names and definitions are to be confirmed by inspecting the files and recorded in a data dictionary.
Known risk: the CAA has introduced a new method for calculating its punctuality measure. Older months may not be directly comparable with newer ones. The project must identify the change point and flag it on charts rather than silently blending the series.
8. Functional requirements
Pipeline
• FR-1: Download the monthly CAA files for the chosen period with a single command, and store raw files unchanged.
• FR-2: Parse and standardise airport names, airline names, route labels, dates and units.
• FR-3: Load clean data into PostgreSQL with a documented schema and keys.
• FR-4: Run data-quality checks on every load and write the results to a log table.
• FR-5: Be re-runnable, so adding a new month needs no code change.
Data-quality checks
• DQ-1: Delay-band shares for each row sum to approximately 100%, within a stated tolerance.
• DQ-2: Cancelled flights never exceed total flights.
• DQ-3: No duplicate rows for the same airport, airline, route and month.
• DQ-4: No missing months inside the chosen range.
• DQ-5: Airport and airline names map to a controlled list, and unmapped values are reported.
• DQ-6: Totals in the detailed file reconcile with the summary file within tolerance.
• DQ-7: Outliers (for example, extreme average delay) are flagged for review, not deleted.
KPIs (SQL views)
• On-time performance: share of flights on time, using the CAA's published definition, stated verbatim in the KPI sheet.
• Average delay in minutes.
• Cancellation rate.
• Delay-band distribution.
• Month-on-month and year-on-year change for each KPI.
• Heathrow's rank among the peer set for each KPI.
Peer set (initial): Gatwick, Manchester, Stansted, Luton and Birmingham, to be confirmed against the published airport list.
Dashboard
• Page 1, Overview: Heathrow KPI cards, trend lines, and change versus last month and last year.
• Page 2, Benchmark: Heathrow versus peers on each KPI, with a ranking view.
• Page 3, Airlines and routes: ranked tables and charts of delay and cancellations, with drill-down.
• Page 4, Data quality: results of the checks, the methodology-change marker, and the data source and refresh date.
• Filters on all pages: month range, airline, and arrival or departure.
• A visible CAA attribution on every page.
9. Non-functional requirements
• Reproducible: a clean clone plus documented setup steps reproduces the dashboard.
• Documented: README, data dictionary and KPI definitions are included.
• Clear: every chart has a title, units and a plain-language takeaway.
• Maintainable: the pipeline is modular and tested for the main parsing and quality rules.
10. Success measures
This is a portfolio project, so success means:
• The pipeline runs end to end from a clean setup without manual edits.
• All data-quality checks pass, or the exceptions are documented and explained.
• The dashboard answers all five key questions in section 5.
• A short insights note presents three findings, each with a recommended action.
• The repository is public, with a README, screenshots and CAA attribution.
• A non-technical reader can understand the KPI definitions without help.
11. Deliverables
• Public GitHub repository with pipeline code, SQL, and documentation.
• Power BI dashboard file, plus screenshots or a PDF export for viewers without Power BI.
• Data dictionary and KPI definitions sheet.
• This PRD.
• One-page insights note: three findings with recommended actions.
12. Milestones (approx. 3 working days)
• Day 1: Inspect the files, finalise the schema, build the ingestion pipeline and data-quality checks.
• Day 2: Build the SQL KPI views and the dashboard pages.
• Day 3: Write the insights note, README and data dictionary, polish visuals, and publish the repository.
13. Risks and assumptions
• The CAA's change in calculation method may break comparability across months. Mitigation: identify the change point and mark it clearly.
• File formats or column names may change between months. Mitigation: validate the schema on every load and fail loudly.
• Power BI Desktop runs on Windows only. Mitigation: use a Streamlit dashboard if Power BI is not available.
• Public data cannot explain causes of delay. Mitigation: state this limitation, and avoid causal claims in the insights note.
• Personas are assumed rather than researched. Mitigation: label them as assumptions in all materials.
14. Open questions
• Which months to include, and where does the method change fall?
• Should the primary view focus on arrivals, departures, or both?
• Which peer airports give the fairest comparison?
• Is Power BI or Streamlit the better delivery format for the intended audience?