## DC–DC Converter

In this project, you will design and implement a **60 W DC–DC converter** that supplies a resistive load from a variable DC input. Your converter must regulate its output voltage using closed-loop control and operate from a single external power source.

You are free to choose an isolated or non-isolated topology. A buck converter is one possible solution, but you are encouraged to compare alternatives and justify your choice.

Start working early. You will submit a preliminary design, present it during the feedback session, revise your design, and then submit your PCB files for production. **PCB implementation is mandatory.**

## Deadlines

| Deliverable | Date |
| - | - |
| Pre-Report — Design and Simulation | 15 November 2026 |
| Feedback Session — Design Presentation | 16–20 November 2026 |
| PCB Files for Sponsored Production | 25 November 2026 |
| Hardware Demo | 4 January 2027 |
| Final Report | TBA |

Individual presentation slots will be announced separately.

**The 25 November deadline is for the sponsored PCB production round. Students are responsible for arranging and covering the cost of any later PCB production, including revised boards.** Plan your design revisions and component procurement accordingly.

## Specifications

| Parameter | Requirement |
| - | - |
| Input voltage | 20–48 V DC |
| Nominal output voltage | 12 V DC |
| Rated output current | 5 A |
| Rated output power | 60 W |
| Steady-state output voltage tolerance | ±2% of 12 V: 11.76–12.24 V |
| Output voltage ripple | Maximum 120 mV peak-to-peak: 1% of nominal output voltage |
| Load | Resistive; nominal 2.4 Ω at rated output |
| Control | Closed-loop output voltage regulation |
| External power sources | One |
| Implementation | A PCB designed by your group |
| Minimum demo duration | 5 minutes of continuous operation at rated resistive load |

Your design must meet the rated-load requirements throughout the specified input voltage range. The output must be regulated automatically; manually adjusting the duty cycle as the input changes does not satisfy the closed-loop requirement.

All auxiliary voltages must be derived from the main DC input. This includes supplies for the controller, gate drivers, sensors, and any cooling fans. An additional bench supply, adapter, or USB connection may not power any part of the converter during the final demonstration.

The voltage tolerance and ripple limit apply to steady-state operation. Record the actual output voltage, current, and power during testing. The nominal resistor value alone is not proof that the converter is delivering its rated power.

The common test procedure, including additional load points and ripple measurement settings, will be announced separately.

## Project Steps

1. **Choose your partners.** Each group will consist of **3 students**. You are free to choose your partners.

2. **Create a project repository.** Keep your calculations, simulation files, schematics, PCB design files, bill of materials, reports, measurement results, and any controller code in an organized repository. Keep a record of design revisions.

3. **Select a topology.** Compare suitable converter topologies and discuss their advantages and disadvantages for the specified input and output conditions. Present your selection process in the Pre-Report.

4. **Perform analytical calculations.** Determine the operating range, duty cycle or conversion ratio, switching frequency, inductance, capacitance, and voltage/current stresses on the components. Estimate conduction and switching losses and evaluate cooling requirements. Include magnetic design calculations where applicable.

5. **Run simulations.** Begin with a simple model to verify the power stage. Then include the controller, gate-drive behavior, and relevant component non-idealities. Demonstrate operation at different input voltages and investigate the effect of load changes.

6. **Select components and complete the preliminary design.** Choose the power, control, sensing, gate-drive, and auxiliary-supply components. Check availability and lead times. Prepare a complete schematic, a bill of materials, and an initial PCB layout for the feedback session.

7. **Present your design and implement the feedback.** Explain your design decisions, calculations, simulations, and manufacturing plan. Revise your schematic and PCB layout after the feedback session and document the changes.

8. **Submit your PCB files.** Submit the revised production files by **25 November 2026** to participate in the sponsored production round. Include the Gerber and drill files together with the schematic, PCB source files, and bill of materials. Check component footprints and connections before submission.

9. **Assemble and test your prototype.** Verify auxiliary supplies and gate signals before testing the power stage. Begin with reduced power and increase the load gradually. Provide accessible input/output connections and test points. The final prototype must be implemented on your group's PCB.

10. **Demonstrate and report your results.** On demo day, operate the converter from a single DC source and supply the rated resistive load continuously for at least **5 minutes**, while meeting the output voltage and ripple requirements. Submit a final report comparing your calculations, simulations, and measurements.

## Grading

The base hardware project grade is out of 100 points.

- **Pre-Report — Design and Simulation (15 points):** Present your topology selection, analytical calculations, simulations, control approach, and component selection. Include the auxiliary circuits required to build a complete working converter.

- **Presentation for the Feedback Session (15 points):** Explain your preliminary design, critical component choices, simulation results, initial PCB layout, and implementation plan. Be prepared to discuss design limitations and proposed improvements.

- **Hardware Demo (40 points):** Present your PCB prototype and demonstrate closed-loop operation from a single external source. The minimum operating requirement is continuous operation at rated resistive load for 5 minutes while satisfying the specified output voltage and ripple limits. Demonstrate operation over the specified input range using the common test procedure.

- **Final Report and Test Results (30 points):** Present the final design, changes made after the feedback session, component and thermal calculations, simulation results, and hardware measurements. Include output regulation, ripple, and efficiency measurements. Explain differences between predicted and measured behavior and provide the final design files.

## Bonus Parts

Bonus opportunities are listed below. Your design must meet the minimum project requirements to qualify. **Bonus point values and scoring details not specified below will be announced separately.**

- **Overload Bonus:** Demonstrate operation at **90 W output**, corresponding to **12 V and 7.5 A**, using a resistive load of nominally **1.6 Ω**. Maintain the specified output voltage regulation and ripple limits during the overload test. Support the increased power capability with component-rating and thermal calculations.

- **Current Limit Bonus:** Implement output current limiting for excessive loads and output short circuits. The current-limit target is **5 A** for the standard design, or **7.5 A** for groups pursuing the overload bonus. Demonstrate that the converter limits its output current by reducing the output voltage when necessary. Current limiting must be implemented by the converter itself; relying on the laboratory supply's current limit does not qualify. Record the output voltage and current during the fault and after the fault is removed.

- **Input Reverse Polarity Protection Bonus:** Protect the converter against accidental reversal of the input supply polarity. Demonstrate that the protection prevents damage and that normal operation is restored after the correct polarity is reconnected. Explain the protection circuit and include its losses in the overall efficiency measurement.

- **Topology Bonus:** Implement and justify an alternative converter topology. If no other group uses your converter topology, you will receive the **full topology bonus**. If exactly two groups use the same topology, each group will receive **half of the topology bonus**. If three or more groups use the same topology, those groups will receive **no topology bonus**. Both isolated and non-isolated designs are eligible. Explain the benefits and trade-offs of your choice using calculations, simulations, and hardware measurements. Changing only the controller or switching frequency does not constitute a different power-converter topology.

- **Battery Charging Bonus:** Use the same power stage to demonstrate battery charging in either **constant-voltage (CV)** or **constant-current (CC)** mode. Charging settings must match the selected battery's requirements. CV operation must include a suitable current limit, and CC operation must stop or change mode at the battery's charging-voltage limit. The battery and charging test conditions will be announced separately.

- **Efficiency Bonus:** Improve the overall converter efficiency and support your design decisions with loss calculations and measurements. Measure efficiency at **20, 24, 36, and 48 V input**, at the nominal **60 W output operating point**. Evaluation will use the average of these efficiencies. Input power must include all auxiliary circuits, including the controller, gate drivers, and any cooling fans.

  Calculate the arithmetic mean **η̄ = (η20 + η24 + η36 + η48) / 4**, using efficiencies as fractions between 0 and 1. Average the efficiencies first, then calculate the score:

  - For **η̄ < 0.80:** **Bη = 50 × (η̄ − 0.80)**.

  - For **η̄ ≥ 0.80:** **Bη = 100 × (η̄ − 0.80)**.

  **Negative scores are allowed and are deducted from the project grade; they are not clipped to zero.** Positive scores are added to the project grade. For example, average efficiencies of **70%, 80%, 90%, and 95%** give **−5, 0, +10, and +15 points**, respectively.

- **Line and Load Transient Response Bonus:** Design and compare at least **two controller settings or compensation designs** using both simulation and hardware measurements. Investigate **line response** by changing the input voltage with the resistive load fixed, and **load response** by changing the load with the input voltage fixed. Compare overshoot, undershoot, settling time, and oscillation under the same test conditions, and explain your final design choice. Record the actual input-voltage or load-current change alongside the output response. This bonus rewards a reasoned comparative study rather than ranking groups by response speed.

- **Compactness Bonus:** Present your complete working converter **inside an enclosure**. Commercial project enclosures and custom-designed enclosures, including 3D-printed designs, are both allowed. The power stage, control circuitry, and auxiliary supplies must fit within the enclosure. Compactness will be evaluated using the enclosure's external dimensions: **Volume = Length × Width × Height**. Smaller enclosed designs will be favored. An unenclosed PCB is not eligible for this bonus, and the assembled design must still meet the minimum operating requirements.

- **Karma Bonus:** This individual bonus recognizes the student who contributes most to helping other groups throughout the project. The recipient will be selected through an anonymous vote by the students.

## Frequently Asked Questions

**Can we use an isolated converter?**

Yes. Both isolated and non-isolated DC–DC topologies are allowed. You must justify your topology selection and meet the same input, output, control, and implementation requirements.

**Can we use an analog controller?**

Yes. Analog and digital controllers are both allowed. Closed-loop output voltage regulation is mandatory.

**Can we use a separate supply for the controller or gate drivers?**

All supplies must be derived from the main DC input during the final demonstration. Temporary supplies may be useful during development, but the final system must satisfy the single-source requirement.

**Is a PCB required?**

Yes. A breadboard or stripboard prototype does not satisfy the final implementation requirement. Your group must design its PCB and submit production files after incorporating the feedback.

**What happens if we need another PCB after the sponsored production round?**

You may revise and manufacture another board, but your group is responsible for arranging and paying for any later PCB production. The sponsored production file deadline is **25 November 2026**.

**Do we need a battery for the minimum demonstration?**

No. The required load is resistive. Battery charging is outside the minimum demonstration; any related bonus requirements will be announced separately.

**What DC supply is available in the laboratory?**

The laboratory supply can operate in parallel mode up to **30 V / 6 A**, or in series mode up to **60 V / 3 A**. Select the appropriate mode for your input voltage and current. Stop the test before changing the supply configuration.

**Can we use AI tools?**

Yes. You are encouraged to use AI tools in your simulations and PCB design. However, you must understand what you have done, what you have implemented, and why. You are responsible for checking AI-generated results and must be able to explain and justify your design decisions, calculations, simulations, and implementation.
