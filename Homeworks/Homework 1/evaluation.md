## Guideline for Homework #1

- You will complete the homework in pairs, except for the student assigned to work individually in the final row of [Teams.md](Teams.md).
- Create one **private GitHub repository** in one team member's account and add [Ogün](https://github.com/OgunAltun) as a collaborator. Each partner is required to contribute to the work.
- You may use any simulation software, but MATLAB/Simulink is recommended for this homework.
- Submit a report **in PDF format to ODTUClass**. Include the report, simulation models and any supporting scripts in your GitHub repository. Both the report and source files will be used for grading.
- The report must present your calculations, component selections, simulation results and answers to the questions. Comment on the results for each simulation question.
- Cite all datasheets and other sources used. Reports will be checked using Turnitin, and copying will not be tolerated. Complete the work with your assigned partner, or on your own if assigned to work individually.
- Late submissions will be accepted for one day after the deadline and graded over 85 points (a 15% reduction).

## Evaluation

The homework will be evaluated using the following guideline:

| Category | Weight |
| --- | --- |
| Number of commits and commit quality | 15% |
| Report quality | 5% |
| Technical level | 80% |

The technical rubric below is marked out of 100 and scaled to the 80% technical contribution.

## Q&A Session

Each group is required to attend a **10-minute Q&A session** after submission. Both group members must attend and answer questions individually. The student assigned to work alone must also attend a 10-minute session. The schedule will be announced separately.

The purpose of this session is to evaluate each student's understanding of the submitted work: what they simulated, why they chose particular components and parameters, how they obtained the reported quantities, and what their results mean.

Have your submitted report, simulation models and supporting scripts ready to inspect. You may refer to your submitted work, but you must answer in your own words without assistance from your partner or AI tools. Be prepared to:

- Explain the circuit, simulation setup, assumptions and your own contribution.
- Show how a reported quantity was measured or calculated.
- Interpret a waveform or table and explain the reasoning behind a conclusion in your report.
- Justify a component selection or modelling choice using the relevant calculations or datasheet.
- Predict the effect of a small parameter change and explain how you would verify the prediction in the simulation.

Understanding will be assessed individually based on technical correctness, reasoning and consistency with the submitted work. The answers will inform each student's marks for the relevant parts of the **Technical Level** rubric. Group members may receive different grades.

**If you cannot explain what you did in the homework and why you did it, you will receive a grade of zero for the entire homework, regardless of the quality of the submitted report or simulation files. This rule applies individually to each student.**

## Number of Commits

Each student will be evaluated individually according to their contributions.

- Make meaningful commits on at least two different days. Each qualifying day earns 5 points, up to 10 points.
- A meaningful commit must contain a substantial contribution to the models, calculations, analysis or report. Changing a few words alone is not sufficient.
- Commit timing will be evaluated with common sense. For example, commits at 23:58 and 00:02 will count as one day.
- The remaining 5 points are awarded for clear, explanatory commit messages describing the specific improvements in each version.

Start early and improve your work regularly. See [Writing Good Commit Messages](https://vip.wordpress.com/documentation/commit-messages/) for guidance.

## Report Quality

The report will be evaluated using the following criteria:

- A separate title page.
- A brief introduction explaining the scope and aims of the homework.
- Clear sections and subsections corresponding to the questions.
- Calculations, component-selection reasoning, simulation results and answers to all questions.
- Captions for all figures and tables.
- Graphs with white backgrounds, properly labelled axes, units, legends where needed and readable font sizes.
- Exported simulation figures rather than screenshots where possible.
- Clear writing, correct spelling and grammar, and references to datasheets and other sources.
- Typed equations and explanations. **Photographs of handwritten calculations or comments will not be evaluated.**

Up to 5 points will be awarded for report quality. Reports that do not meet the required quality may be returned for resubmission within one day. Resubmissions and late submissions will be graded over 85 points.

## Technical Level

Credit is based on the correctness of calculations and simulations, suitability of selected components, quality of comparisons, and interpretation of the results. Plots and tables must be supported by comments explaining the observed behaviour.

Simulation settings, measurement intervals, THD settings and the time-step convergence check must be documented. Models and supporting scripts must allow the reported results to be reproduced.

| Question | Topic | Points |
| --- | --- | ---: |
| 1(a) | Single-phase rectifier with resistive load | 6 |
| 1(b) | Capacitor-filter sizing and comparison | 9 |
| 1(c) | Commercial capacitor selection, ESR and losses | 10 |
| 1(d) | Reducing the effect of ESR | 6 |
| 1(e) | Two LC-filter designs and justified selection | 14 |
| **Q1 total** | | **45** |
| 2(a) | Unfiltered three-phase rectifier and harmonics | 7 |
| 2(b) | Source inductance and commutation | 9 |
| 2(c) | Capacitor filtering and comparison | 9 |
| **Q2 total** | | **25** |
| 3(a) | Diode stresses and commercial device selection | 6 |
| 3(b) | Datasheet-based diode model and verification | 8 |
| 3(c) | Simulated and calculated conduction losses | 10 |
| 3(d) | Performance comparison and power balance | 6 |
| **Q3 total** | | **30** |
| **Technical total** | | **100** |
