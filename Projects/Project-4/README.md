# EE 463 PROJECT#4

## DC/DC CONVERTERS

### Deadline: 21/12/2019 23:59

Please check [Teams.md](Teams.md) and [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add me(/ozank), Gökhan(/gkhnckl) or Furkan(/furkankarakaya) as a collaborator.

<br />

**1) Buck Converter**<br />

A step-down DC/DC converter will be used in regulated power supply. The specifications are; the input voltage range is 6-24 V and the output voltage is fixed at 3.3 V. The output voltage control is maintained by means of feedback control. The switching frequency is selected as 250 kHz. The L and C filter components are given as 18 µH and 220 µF. Assume ideal components, ignore all parasitic effects and assume ideal switches.


 **a)** Find the load current that guarantees CCM operation under all operation conditions. Don't just use the formula; derive your steps.

**b)** Assume that rated output power is 5 W. Calculate the maximum inductor current ripple and output voltage ripple for the given input voltage range.

**c)** Simulate the steady-state behavior of the converter and show the important waveforms for boundary conduction mode with 15 V of input voltage. Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Pre-filtered output voltage
* Diode voltage and current
* Switch voltage and current


**d)** Repeat (c) with 12 V input and rated output power of 5 W. Comment on the results.

**e)** Repeat(c) with 6 V input and 0.33 W output power. Comment on the results.

**f)** What is inrush current, define it. Considering the case in (e), what is your inrush current at input current for this case. Propose a method to avoid inrush current and implement your solution to your simulation model. Compare the results by plotting the cases in this part and part (e).

**g)** Now, consider that the output capacitor has 100 mΩ ESR parasitics. Simulate the rated load at 12 V input voltage. Compare the results with ideal case of part (d) by plotting the output voltage with and without ESR and also plot capacitor current. Comment on the effect of adding capacitor ESR to the converter parameters such as output voltage ripple.


**2) Boost Converter**<br />

In step-up DC/DC converter, let input voltage range be 10-20 V and output voltage be 24 V with switching frequency of 500 kHz. Assume that rated output power is 48 W.

**a)** Consider all components as ideal. Calculate minimum inductance that will keep the converter operating in the CCM operation for output power of 10 W.

**b)** Calculate the output capacitance for peak-to-peak voltage ripple less than 2% under rated output power.

**c)** Simulate the steady-state behavior of the converter and show the important waveforms for boundary conduction mode of (a). Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Pre-filtered output voltage
* Diode voltage and current
* Switch voltage and current

**d)** Repeat (c) under rated output power and input voltage of 10 V. Comment on the results.

**e)** Assuming the switches and capacitors are ideal, but the inductor has 57 mΩ ESR, and considering the load resistance is equal to the rated load resistance, derive the voltage gain as a function of the duty cycle. Show your steps clearly. On the MATLAB, plot the voltage gain with and without ESR on the same graph as a function of duty cycle. Comment on the results. You may verify these results via simulation and for this you may choose an input voltage of 15 V.

**f)** Repeat the same steps in (e) for the converter efficiency.


**3) Feedback (Bonus)**<br />

How much time did you spend for this homework?
