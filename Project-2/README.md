# EE 463 PROJECT#2

## Controlled Rectifiers

### Deadline: 16/12/2018 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project.

Throughout this homework, assume the rectifiers are connected to Turkish grid (400 V l-l, 50 Hz). Note that, single-phase rectifiers are connected to Phase-Neutral. When a single-phase diode rectifier is mentioned, it is energized with a phase and neutral connection.

### Q1) Single Phase Controlled Rectifier

Consider the single phase rectifier topologies shown below:

![](single_phase_rectifiers.png)

where R<sub>L</sub> = 4 Ω, L<sub>L</sub> = 200 mH, L<sub>s</sub> = 0.5 mH.

**a)** Calculate analytically the required firing angle α which results in an average output current value of 40 A for both topologies given above, and verify your calculations with simulations.

**b)** Plot V<sub>s</sub> and I<sub>s</sub> on the same graph and find the THD value of I<sub>s</sub> for both topologies.

**c)** Compare the topologies wrt to their advantages, disadvantages and their application areas. Discuss their operational similarities and differences.

### Q2) DC Motor Drive

A PM DC motor is fed from a three-phase grid via a three phase full bridge diode rectifier. Mechanical load driven by the motor is fixed at 24 N.m. Motor data is as follows:

- Field Type: Permanent Magnet
- Armature resistance, Ra = 10 Ω
- Armature inductance, La = 0.01 H
- Back-emf Constant: 0.3 V/rpm
- Motor Inertia: 0.4 kgm2

Other necessary data for the system is as follows:

- Diode forward voltage, Vf = 0.8 V
- Diode on resistance, Ron = 20 mΩ
- Source inductance, Ls = 100 µH
- Source resistance, Rs = 100 mΩ

You can assume default values (of Simulink block), for any parameters not mentioned. Please note that, there are more than one DC-motor models in Simulik, please use [this one](https://www.mathworks.com/help/physmod/sps/powersys/ref/dcmachine.html).

Hint: If you have stability issues with the motor, you can apply load torque a little after the motor is started, or you can play with the initial conditions of the supply or DC-link capacitors etc.

**a)** Plot armature current, speed and torque of the motor from stand-still (zero speed) to steady-state. The graphs should be similar to the ones below. 

![](dc_motor_current.jpg)

**b)** Comment on characteristics (ie frequency, magnitude etc ) of the torque ripple. Find line current THD (at the steady state).

**c)** Propose two methods in order to reduce the torque ripple below 10% of the average torque. Simulate the methods and discuss pros and cons of these methods.


**d)** Find the overall drive efficiency (mechanical power output / electric power input) at steady state. Identify the sources of power loss and make a chart that shows percent share of each loss type in the motor drive. 

Optional: Include the motor efficiency to your calculations as well.

## Q3) Alternative Rectifier Topologies

Consider the power conversion topology depicted below:

![](q3.gif)

**a)** Find the name of the topology and describe its operation and application areas. If you find other variations of this power conversion topology, briefly state them and discuss the differences.


**b)** Compare this topology with the full bridge diode rectifier by simulating them both. For a good comparison, arrange the operating conditions such that they both produce the same average output voltage and average load current values for a resistive load of 10 Ω. Discuss pros and cons.

**Hints:** 

- Do not forget to include “powergui” box to your model.

- You can find the DC motor model from Simscape → Power Systems → Special Technology → Fundamental Blocks → Machines

- For the AC source, use “Three-Phase Source” block.

- There may be different resistor, capacitor, inductor models some of which may be inoperable with your models. Search for “Series RLC Branch” when you need to model a passive element (it can be arranged to any R, L, C or their combinations).

**Important:** While documenting your simulation results, it is often
necessary to make visual arrangements on the graph (zoom in/out, axis
scales, background color, markers etc..). When plotting a periodic
signal, a few repetitions of the full period is enough, i.e. do not plot
a 50 Hz waveform for several seconds as it makes no sense. Unless it is
stated otherwise, document only the steady state values.
