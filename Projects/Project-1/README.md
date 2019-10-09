# EE 463 PROJECT#1

## Single Phase Diode Rectifiers

### Deadline: 24/10/2019 23:59


Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add me(/ozank), Furkan(/furkankarakaya) and Gökhan(/gkhnckl) as a collaborator.

**Important:** While documenting your simulation results, it is often
necessary to make visual arrangements on the graph (zoom in/out, axis
scales, background color, markers etc..). Unless otherwise stated, plot your graphs in steady state and for two periods only. Axes should be properly labeled and visible.
It is recommended to use the library (Simscape->Power Systems->Specialized Technology) in Simulink.


**1) Single phase half bridge rectifier**<br />
Consider the half wave rectifier shown below.

![](half_wave.jpg)

Simulate the circuit fed with a resistive load of R = 100 Ω. Ignore any non-idealities and take AC source as Turkish Electricity Grid phase-neutral voltage.

**a)** Plot the output voltage waveform for step times of 1ns, 0.5ms and 5ms.

**b)** Comment on the significance of step time in computer simulations. Which one would you prefer for this question? Comment on the advantages and disadvantages of the selection of step time too small or too large.

**c)** Analytically, calculate the output average voltage and input current THD.

**d)** Using simulation tools, obtain the above quantities in part (c). Compare your analytical results with simulation results. Comment on the results.


---

**2) Single phase full bridge diode rectifiers** <br />
Consider the full bridge rectifier shown below.

<img src="full_bridge.PNG" width="400">

**a)** What do Ls and Rs represents in practical applications?

**b)** Using simulation tools, find the minimum output filter capacitance to have 5% output voltage peak-to-peak ripple to mean ratio. Use the values of Vs=230V AC at 50Hz, Ls=1mH, Rs=1mΩ and Rload=100Ω. Assume diodes are ideal.

**c)** Plot the output voltage, input voltage and current at the same graph.

**d)** Measure average of output voltage, input current THD and power factor.

**e)** Simulate the same circuit without Rs and Ls and observe and state the differences. What is the effect of these two?

**f)** Observe and record the stresses on the diodes for the case on part (e). Pick a real diode using manufacturers' datasheet.

**Hint:** When you need to find a commercial product, you can search the database of “Digikey”, which is a big retailer for electronic components, from [**Digikey.com**](https://www.digikey.com/).<br />
*Alternatively, you can search other big retailers such as Farnell and Mouser.*

**f)** Input the selected diode parameters into the simulation, then measure the rectifier efficiency for the case in part (e).

---

**3) Three phase full bridge diode rectifiers** <br />
Consider the three phase rectifier shown below.

<img src="three_phase.PNG" width="350">


**a)** Simulate the circuit for Ls=0, Van, Vbn and Vcn are balanced three phase voltages at 50 Hz, ideal diodes and Id=40 A. Plot the output voltage and phase A input current on the same graph.

**b)** Analytically, calculate the output voltage average and compare with simulation results. Comment on any differences.

**c)** Perform the harmonics analysis, i.e. find the harmonic content of output voltage and input current up to 30th harmonic of line frequency. Comment on your findings. (*Hint: Use powergui block for harmonics analysis.*)

**d)** Simulate the same rectifier for Ls=1mH and plot the output voltage and input current. Observe the effect of line inductance and comment on your observations.

**e)** Repeat part (b).

**f)** Compare the harmonic content of the input current for different Ls values 0, 1mH, 10 mH cases. Comment on the differences.

---

**4) Feedback (Bonus)** <br />
How much time did you spend for this homework?
