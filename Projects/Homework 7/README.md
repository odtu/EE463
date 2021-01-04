# EE 463 Homework#7

## Boost Converter

### Deadline: 13/1/2021 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add Tokgoz(/tokgozfurkan) and Karakaya(/furkankarakaya) as a collaborator.

<br />

**1) Boost Converter**<br />

In step-up DC/DC converter, let input voltage range be 10-20 V and output voltage be 24 V with switching frequency of 500 kHz. Assume that rated output power is 48 W.

**a)** Consider all components as ideal. Calculate minimum inductance that will keep the converter operating in the CCM operation for output power of 10 W. Don't just use the formula, derive your steps.

**b)** Calculate the output capacitance for peak-to-peak voltage ripple less than 2% under rated output power.

**c)** Simulate the steady-state behavior of the converter and show the important waveforms for boundary conduction mode of (a). Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**d)** Assuming the switches and capacitors are ideal, but the inductor has 57 mΩ ESR, and considering the load resistance is equal to the rated load resistance, derive the voltage gain as a function of the duty cycle. Show your steps clearly. On the MATLAB, plot the voltage gain with and without ESR on the same graph as a function of duty cycle. Comment on the results. You may verify these results via simulation and for this you may choose an input voltage of 15 V.

**e)** Repeat the same steps in (d) for the converter efficiency.

**f)** Choose semiconductor products -switches, diodes- that is appropriate for your design. Calculate the losses on these devices for rated power operation with 15 V input voltage.

**g)** Using the calculated loss values, construct a thermal lumped element model and estimate the junction temperature without a heatsink. If necessary, choose a thermal interface material and heatsink and find out the junction temperature with these materials. Clearly state any assumption that you made.

**2) Feedback (Bonus)**<br />

How much time did you spend for this homework?
