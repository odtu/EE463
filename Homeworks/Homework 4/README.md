# EE 463 Homework#4

## DC/DC CONVERTERS

### Deadline: 14/01/2022 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add [me](https://github.com/tokgozfurkan) as a collaborator.

<br />

**1) Buck Converter**<br />

A step-down DC/DC converter will be used in regulated power supply. The specifications are; the input voltage range is 6-24 V and the output voltage is fixed at 3.3 V. The output voltage control is maintained by means of feedback control. The switching frequency is selected as 250 kHz. The L and C filter components are given as 18 µH and 220 µF. Assume ideal components, ignore all parasitic effects and assume ideal switches.


 **a)** Find the load current that guarantees CCM operation under all operation conditions. Don't just use the formula; derive your steps.

**b)** Assume that rated output power is 5 W. Calculate the maximum inductor current ripple and output voltage ripple for the given input voltage range.

**c)** Simulate the steady-state behaviour of the converter and show the important waveforms for boundary conduction mode with 15 V of input voltage. Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**d)** Repeat part C with 12 V input and rated output power of 5 W. Comment on the results.

**e)** Repeat part C with 6 V input and 0.33 W output power. Comment on the results.

**f)** What is inrush current, define it. Considering the case in part E, what is your inrush current at input current for this case. Propose a method to avoid inrush current and implement your solution to your simulation model. Compare the results by plotting the cases in this part and part E.

**g)** Now, consider that the output capacitor has 100 mΩ ESR. Simulate the rated load at 12 V input voltage. Compare the results with ideal case of part D. Comment on the effect of adding capacitor ESR to the converter parameters such as output voltage ripple. Also, offer a solution to decrease the equivalent ESR of the output capacitor and to reduce the output voltage ripple.

**2) Boost Converter**<br />

In step-up DC/DC converter, let input voltage range be 10-20 V and output voltage be 24 V with switching frequency of 500 kHz. Assume that rated output power is 48 W.

**a)** Consider all components as ideal. Calculate minimum inductance that will keep the converter operating in the CCM operation for output power of 10 W.

**b)** Calculate the output capacitance for peak-to-peak voltage ripple less than 2% under rated output power.

**c)** Simulate the steady-state behaviour of the converter and show the important waveforms for boundary conduction mode of part A. Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**d)** Assuming the switches and capacitors are ideal, but the inductor has 57 mΩ ESR, and considering the load resistance is equal to the rated load resistance, derive the voltage gain as a function of the duty cycle. Show your steps clearly. On the MATLAB, plot the voltage gain with and without ESR on the same graph as a function of duty cycle. Comment on the results. You may verify these results via simulation and for this you may choose an input voltage of 15 V.

**e)** Repeat the same steps in Part D for the converter efficiency.

**f)** Choose commercial semiconductor products using Digikey that is appropriate for your design. Calculate the losses on these devices for rated power operation with 15 V input voltage. How would losses on the diode and switch change if the duty cycle is increased? Explain in detail.

**g)** Using the calculated loss values, construct a thermal lumped element model and estimate the junction temperature without a heatsink. If necessary, choose a thermal interface material and heatsink and find out the junction temperature with these materials. Clearly state any assumption that you made.
