# EE 463 PROJECT#1

## Single Phase Diode Rectifiers

### Deadline: 25/11/2018 23:59


Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project.

Throughout this homework, assume the rectifiers are connected to Turkish grid (400 V l-l, 50 Hz). Note that, single-phase rectifiers are connected between phase and neutral.

**1)** Simulate a single-phase diode rectifier feeding a resistive load
of R = 100 Ω. 
For the computation, choose a discrete time step calculation in the simulation settings. Choose the step size 1.5 msec, 10 µsec and 1 µsec respectively, and compare the results and comment on the differences. What is the importance of step size in a digital simulation environment?

**2)** Simulate a single-phase diode rectifier for the following loads;

- A resistive load of R = 25 Ω

- An RL load of R = 25 Ω , L = 10 mH

- An RL load of R = 25 Ω , L = 1 H

**2.1.** Plot the output voltage waveforms at steady state and obtain the average value of the output voltage and THD of the line current. Compare the results and comment on the differences between different types of loads.

**2.2.** Choose a commercially available diode for this converter. Find both a discrete (single) diode and a single phase diode rectifier module. In your report, state their product codes, links and justify your selection by using important paramanets from the datasheet. Make a comparison between these two possible choices ( 4 discrete diodes or a rectifier module).

**Hint:** When you need to find a commercial product, you can search the database of “Digikey”, which is a big retailer for electronic components, from [**https://www.digikey.com/**](https://www.digikey.com/) *. Alternatively, you can search other big retailers such as Farnell and Mouser.*

**2.3.** Assume an RC loaded rectifier with R = 100 Ω. Find the required capacitance value which yields an output voltage ripple smaller than 20% of the average output voltage. Choose also a commercial capacitor suitable for that circuit. 

*Hint:* Among different types of capacitors, search in the “aluminum electrolytic capacitors” category. State the product code and provide its datasheet.

**2.4.** Repeat the R = 25 Ω , L = 1 H load case with a line inductance of L<sub>S</sub> = 10 mH and compare the results without the line inductance and comment on the differences.

**2.5.** Consider the case depicted in Figure 5.25 of your textbook(Mohan). Assume the load resistance R = 25 Ω, and the line inductances L<sub>S1</sub> = L<sub>S1</sub> = 600 µH. Draw the voltage at the point of common coupling (PCC) and comment on the waveform.

----

**3)** Consider the case depicted in Figure 1, where there are three
single-phase diode bridge rectifiers connected to each phase of the system. Each rectifier feeds its own RC load of R = 200 Ω , C = 470 µF. Line inductances are L = 600 µH.

![](project1_fig.png)
Figure 1. Single-phase diode rectifiers operated from a three-phase grid with neutral connection.*

**3.1.** Find the PF and THD of input current. Plot the waveforms for
Phase A current, neutral wire current and “Diode Bridge 1” output
voltage.

**3.2.** Find RMS values of line currents and neutral current. Comment on
the results.

**3.3.** Repeat for L<sub>S</sub> = 0. Comment on the results.

**Important:** While documenting your simulation results, it is often
necessary to make visual arrangements on the graph (zoom in/out, axis
scales, background color, markers etc..). When plotting a periodic
signal, a few repetitions of the full period is enough, i.e. do not plot
a 50 Hz waveform for several seconds as it makes no sense. Unless it is
stated otherwise, document only the steady state values.*
