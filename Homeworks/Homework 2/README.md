# EE 463 Homework#2

## Device Parameters

### Deadline: 24/11/2024 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add [Ogün](https://github.com/OgunAltun) as a collaborator.

**1) Diode parameters**<br />
 **a)** Define the 5 important power diode characteristics with their symbol and meanings.

[Example: I<sub>ave</sub> is the diode forward average current, defined under nominal operating conditions (say 75C if it is defined so), and it signifies...) ].<br />

**b)** Explain the losses of diodes. Which parameters affect the losses? 

**c)** Select diodes with around 0.5A, 5A, and 50A current ratings. (at most 3 different types/samples for each current rating, considering different speed, different voltage rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

Hint: You can search devices through Digikey, Mouser, Farnell etc. or through the webpages of manufacturers such as Infineon, Semikron, IXYS, Fairchild, International Rectifier, Microsemi, Mitsubishi, Fuji, Toshiba, ABB, ST, Cree...<br />

**d)** Select diodes with around 10V, 100V, and 1000V voltage ratings. (at most 3 different types/samples for each voltage rating, considering different speed, different current rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**e)** By referencing the selected diodes in part 1.c and 1.d, comment on the trade-offs of the diode parameters in detail. How does other parameters change when voltage and current ratings are increased? What may be the advantages and/or disadvantages of choosing an overdesign diode -for example, choosing a diode with 50A current rating to a design with a 2A current? Explain in detail.

[Example: Select two diodes with same voltage and different current ratings. Put these two in a small table and compare the effect of varying voltage on other diode parameters.]

**2) MOSFET parameters**<br />

**a)** Define the 5 most important power MOSFET characteristics with their symbol and meanings.

**b)** Explain the losses of MOSFETs. Which parameters affect the losses? 

**c)** Select MOSFETs with around 0.5A, 5A, and 50A current ratings. (at most 3 different types/samples for each current rating, different voltage rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**d)** Select MOSFETs with around 10V, 100V, and 1000V voltage ratings. (at most 3 different types/samples for each voltage rating, considering different current rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**e)** By referencing the selected MOSFETs in part 2.c and 2.d, comment on the trade-offs of the MOSFET parameters in detail. How does other parameters change when voltage and current ratings are increased? What may be the advantages and/or disadvantages of choosing an overdesign MOSFET? Explain in detail.

**3) Buck Converter**<br />

A step-down DC/DC converter will be used in regulated power supply. The specifications are; the input voltage range is 20-28 V and the output voltage is fixed at 12 V. The output voltage control is maintained by means of feedback control. The switching frequency is selected as 250 kHz. The L and C filter components are given as 10 µH and 5 µF. Assume ideal components, ignore all parasitic effects and assume ideal switches.

**a)** Find the load current that guarantees CCM operation under all operation conditions. Don't just use the formula; derive your steps.

**b)** Assume that rated output power is 25 W. Calculate the maximum output voltage ripple for the given input voltage range.

**c)** Simulate the steady-state behaviour of the converter and show the important waveforms for V<sub>in</sub>=24 V, V<sub>out</sub>=12 V, P<sub>out</sub>=5 W. Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**d)** What is inrush current, define it. Considering the case in part-d, what is your inrush current at input current for this case. Propose a method to avoid inrush current and implement your solution to your simulation model. Compare the results by plotting the cases in this part and part-d.

**4) Boost Converter**<br />

In step-up DC/DC converter, let input voltage range be 10-16 V and output voltage be 20 V with switching frequency of 200 kHz. Assume that rated output power is 25 W. Output capacitance is 20 uF.

**a)** Consider all components as ideal. Calculate minimum inductance that will keep the converter operating in the CCM operation for rated output power.

**b)** Simulate the steady-state behaviour of the converter and show the important waveforms for boundary conduction mode of part-a. Plot following waveforms and comment on the results.
* Inductor voltage and current
* Output voltage
* Diode voltage and current
* Switch voltage and current

**c)** Assuming the switches and capacitors are ideal, but the inductor has a non-zero ESR, derive the voltage gain as a function of duty cycle (d), inductor ESR (r) and load resistance (R<sub>Load</sub>). Show your steps clearly. On the MATLAB, plot the voltage gain with and without ESR on the same graph as a function of duty cycle assuming that ESR is 100 mΩ and rated load is connected. Comment on the results.

**d)** Repeat the same steps in part-c for the converter efficiency.

