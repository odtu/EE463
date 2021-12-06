# EE 463 Homework#3

## DC Motor Drive

### Deadline: 19/12/2020 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add me (/tokgozfurkan) as a collaborator.

**1) Motor Drive**<br />
After graduation, you have started to work Hebelsan AŞ. Your work is to design motor drives for the company. Your boss, who is a very strict and stingy person, wants from you to design a motor drive for a separately excited DC motor with following specifications:

- Rated speed: 1750 RPM
- Rated voltage: 500 V
- Rated power: 3.7 kW
- Armature resistance: 11.2 Ohm
- Armature inductance: 121.5 mH
- Field resistance: 281.3 Ohm
- Field inductance: 156 H
- Field-armature mutual inductance: 1.976 H
- Field voltage: 300 V
- Inertia: 0.02215 kg.m<sup>2</sup>
- Coulomb friction torque: 0.5161 N.m
- Viscous friction coefficient: 0.002953 N.m.s

You have a single phase and a three phase voltage sources with 230 V<sub>rms,l-n</sub> at 50 Hz. Also, you have DC voltage source to excite field winding of the DC machine.

 **a)** After checking the warehouse, you found 4 already built devices with appropriate input voltage and current ratings:
 - Single-phase half-bridge controlled rectifier,
 - Single-phase full-bridge controlled rectifier,
 - Three-phase half-bridge controlled rectifier,  
 - Three-phase full-bridge controlled rectifier.


  Which of the rectifier circuits is suitable for rated power operation of the DC machine? Explain and show the analytical calculation why other rectifiers are not suitable.

**b)** Calculate the firing angle for the chosen topology to achieve rated voltage of the DC machine at the output of the rectifier?

**c)** Simulate the designed circuit on Simulink. Enter the firing angle that you have calculated at part 1.b. Assume that the DC machine works in the rated power conditions. Plot the input voltage and input current of the rectifier on the same graph at steady state. Present the FFT analysis results of the input current. Comment on the results.

**d)** Plot the output voltage and the output current of the rectifier on the same graph at steady state. Plot the speed and the torque of the DC machine at steady state. Comment on the results.

**e)** Plot the input current of the armature of the DC motor at transient part. What might be a problem with the resultant current graph? Propose a method to overcome the problem. Explain it in detail.

**f)**  Assume that there is a 10 mH line inductance on each phases. Calculate the required firing angle to maintain the rated voltage of the DC machine.

**g)**  Show that the output voltage is remained unchanged. Repeat the part c. Comment on the results.

**h)** Propose a method to drive the DC machine in reverse direction as well. Explain it in detail.
