# EE 463 Homework#3

## Duty Controlled Full Bridge Isolating Converter Design

### Deadline: 07/01/2026 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add [Ogün](https://github.com/OgunAltun) as a collaborator.

You are asked to design a 250 W duty controlled full bridge isolating converter with 100 V<sub>in</sub> and 24 V<sub>out</sub> with 1% output voltage ripple (peak-to-peak). Switching frequency of the converter is 200kHz.

**1) Circuit parameters**<br />

  **a)** Assuming the duty cycle of the primary switches is 0.45, find the turns ratio of the transformer.

  **b)** Find the required inductance value so that the filter inductor current ripple is 10% of the average inductor current.

  **c)** Find the output capacitor value to meet the output voltage ripple requirements. Do not just use the formula, show derivation.

  ![](fullbridgeconverter.png)

**2) Magnetic Design**<br />

The total loss of magnetic components -transformer and inductor- should not exceed 15 W and fill factor of the cores should not be less than 30%.

It is strongly advised to use programs such as Matlab or Excel, since magnetic design can be a tedious job which may require a few iterations to find the optimum parameters. A simple script would save you from losing your precious hours.

  **a)** Design your transformer with cores which can be found on [Magnetics](https://www.mag-inc.com/Products/Ferrite-Cores/Ferrite-Shapes). Clearly indicate the reasoning behind choosing the core. Find the primary and secondary number of turns. Calculate the magnetizing inductance of the transformer. (Hint: Magnetics has some great design guides for inductor and transformer designs. Please have a look at those guidelines.)

  **b)** With current density being 4 A/mm<sup>2</sup>, find suitable [AWG cable](https://www.powerstream.com/Wire_Size.htm) according to the switching frequency and current value. Firstly, calculate the fill factor of the transformer with the chosen cable. Is it a reasonable value? Then, calculate the cable DC and AC resistances and copper loss of the transformer (Calculate AC resistance considering skin depth only. Proximity can be ignored).

  **c)** Calculate the core loss of the transformer using core loss formulas given by the manufacturer and compare it with previously found copper loss value. Does your design require new iterations?

  **d)** Design the output inductor with cores on [Magnetics](https://www.mag-inc.com/Products/Powder-Cores/Kool-Mu-Cores). Find the required number of turns and make sure that core is not saturated by checking the DC bias curves of the material.

  **e)** Choose appropriate AWG cable for the design with 4 A/mm<sup>2</sup> current density and calculate the fill factor. Is it a reasonable value? Then, calculate the cable DC and AC resistances and copper loss of the inductor.

  **f)** Calculate the core loss of the inductor and compare it with previously found copper loss value. Does your design require new iterations?

**3) Simulation**<br />


  **a)** Construct a simulation with calculated cable resistances of the inductor and transformer. Check if the circuit meets the requirements. Plot the following waveforms. Comment on the results and explain if you observe any discrepancy from analytical calculations. Also find the required rating of the semiconductors and capacitor according to simulation. You do not need to select commercial products for this part.

  * V<sub>o</sub>
  * V<sub>P</sub>
  * V<sub>x</sub>
  * V<sub>L</sub>
  * i<sub>L</sub>
  * V<sub>sw1</sub>

  **b)** Real transformers have leakage inductances as a small portion of the magnetizing inductance. What would you observe in real case scenario with leakage inductances. Comment on it.

  **c)** Now choose commercial products for semiconductors (MOSFETs and Diodes). Calculate the conduction and switching losses of each device using datasheet parameters.
  
  * Assume an ambient temperature of 40°C.
  * Based on your calculations and thermal characteristics of your selected packages, decide whether you need a heatsink.
  * If a heatsink is required, select a proper one and show that the junction temperature remains below the safety limit at rated load.

  **d)** Assume that you need a bidirectional power flow between input and output sources. What modification is required for this application? Compare the modified topology with your first design. You do not need to simulate the converter.
