# EE 463 Homework#6

## Buck Converter

### Deadline: 3/1/2020 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add Tokgoz(/tokgozfurkan) and Karakaya(/furkankarakaya) as a collaborator.

<br />

**1) Buck Converter**<br />

A step-down DC/DC converter will be used in regulated power supply. The specifications are; the input voltage range is 6-24 V and the output voltage is fixed at 3.3 V. The output voltage control is maintained by means of feedback control. The switching frequency is selected as 250 kHz. The L and C filter components are given as 18 µH and 220 µF. Assume ideal components, ignore all parasitic effects and assume ideal switches.

 **a)** Find the load current that guarantees CCM operation under all input voltage conditions. Don't just use the formula; derive your steps.

**b)** Assume that rated output power is 5 W. Calculate the maximum inductor current ripple and output voltage ripple for the given input voltage range.

**c)** Calculate the value of the load resistance such that the converter works on the boundary conduction mode with 15 V of input voltage. Simulate the steady-state behavior of the converter and plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**d)** Calculate the load resistance of the converter with 12 V input and rated output power of 5 W. Simulate the steady-state behavior and plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**e)** Calculate the load resistance of the converter with 6 V input and rated output power of 0.33 W. Simulate the steady-state behavior and plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**f)** Define the term "inrush current". Considering the case in (e), what is your inrush current at input current for this case. Propose a method to avoid inrush current and implement your solution to your simulation model. Compare the results by plotting the cases in this part and part (e).

**g)** Now, consider the case in part (d) such that the output capacitor has 100 mΩ ESR. Simulate the rated load at 12 V input voltage. Compare the results with ideal case of part (d). Comment on the effect of adding capacitor ESR to the converter parameters.

**2) Feedback (Bonus)**<br />

How much time did you spend for this homework?
