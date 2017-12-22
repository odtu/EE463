# EE 463 PROJECT#3

## 3-Phase Thyristor Rectiers and DC/DC Converters

### Deadline: 05/01/2018 23:59


Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project.

### Q1) 3-Phase Thyristor Converter

A DC motor is fed from a three-phase grid via a three phase full bridge (fully controlled) thyristor rectifier. Mechanical load driven by the motor is fixed at 25 N.m (which can be delayed for start-up process). Motor data is as follows:

- Armature resistance, Ra = 10 Ω
- Armature inductance, La = 0.01 H
- Field resistance, Rf = 300 Ω
- Field inductance, Lf = 156 H
- Field-armature mutual inductance, Laf = 2 H
- Other necessary data for the system is as follows:
- Thyristor forward voltage, Vf = 0.8 V
- Thyristor on resistance, Ron = 20 mΩ
- Source inductance, Ls = 100 µH
- Source resistance, Rs = 100 mΩ

For the parameters not mentioned here but seen on dialogue boxes of the simulation models, you can assume the default values. For simplicity, you can utilize an auxiliary DC power source providing 300 V for field excitation.

You are required to design a speed controller, which feeds the controlled rectifier with a proper delay angle (α) such that commanded speed reference is met. To test the effectiveness of the controller you designed, apply the following driving performance test: Start the motor with a speed reference of 150 rad/sec. After the motor reaches its steady state speed value of 150 rad/sec, change the speed reference to 75 rad/sec. Finally, speed reference is set to 150 rad/sec again. Simulation is completed when the motor reaches steady state.

Plot armature current, speed and torque waveforms on separate graphs but sharing the same time axis (the style used in the previous homework). You may want to change page orientation while documenting the graph for increased visual clarity. Comment on the results. You can develop further driving scenarios and comment on their results too.

**Hints for Simulink:**

- You can use the models that you developed for the previous homework as a starting point. We will be using the same DC machine (remember that its armature inductance value was updated to be 0.01 H, correct if necessary). For the model of thyristor controlled rectifier, you can simply change the switch type from diode to thyristor in the rectifier block and the input port for gating signals will automatically appear.

- Search for “6-pulse” in the Simulink Library Browser. It is a model that you can use to create required gating pulses of specified time delay. Click on “Help” button of the block to access further information and application examples.

- A simple PI controller will suffice for speed control. It is required to create the specific time delay such that controlled output voltage yields the desired speed value. Do not forget to include upper and lower limits for PI output. Avoid a very fast acting controller in the beginning as it may lead to large swings at its output hence oscillations. After a slow but stable control is established, you can tune it for better dynamic performance.


**Note:** You may also use PSIM if you want.

### Q2) Buck Converter

Design and simulate a Buck converter using a power MOSFET with the following specs: VIN = 56V, VOUT = 28V, RLOAD = 4Ω (fixed). You can run the converter with an “open loop” approach, i.e. by providing a fixed duty cycle of proper value, which yields the desired output voltage at steady state, without designing any control loops.

Choose a reasonable switching frequency. Design your converter with commercial circuit elements and with their product codes, their costs and important parameters listed.

Simulate and plot the graph depicting the steady state performance of the converter you designed (in the simulations you can use ideal device models). 

State ΔVOUT, ΔIL. Find the overall cost. By going through the devices’ datasheets, evaluate overall efficiency at steady state. Comment on the results.

### Q3) Boost Converter (Webench)

WEBENCH is a digital platform created by Texas Instruments to design and simulate converters online. You can reach the platform through the following link: [webench.ti.com](http://webench.ti.com) . Please note that, registration is required to use and to save your designs on WEBENCH.

In order to become familiar with WEBENCH and learn the straight forward design method which is commonly preferred in industry, you are supposed to design a step-up converter as known as boost converter using this platform. For the design, the input parameters are given in Table 1. 

| Vin  | 5± 0.2 V |
| Vout | 12 V     |
| Pout | 24 W     |
| Tamb | 25⁰C     |
Table 1: Input Parameters


3.1) The parameters, which are given in Table 1, will be used as a starting point for your design. As expected, there will be many design options with different characteristics (efficiency, output ripple, cost etc.). Therefore, you are required to develop your design strategy as if you are a design engineer in a company. For this purpose, a very useful graph named as “Advanced Charting” is given on WEBENCH (see the left panel). Please, explain your design strategy and how the design constraints are selected. Plus, attach the corresponding charting to your results.

3.2) After determining the design strategy, choose the most advantageous solution and click on “Open Design”. Record the following results for your selection. 

- Circuit Schematic (click on the schematic button at the top panel)
- Efficiency vs Output Current Graph (click on the charts button at the top panel)
- Output Voltage Ripple vs Output Current Graph (click “View Other Charts” in the same panel)

Afterwards, go to the “Op Vals” button at the top panel and fill the Table 2 given below. In the same page, select “Power” for category and share the power loss graph for circuit elements.

- Inductor Current Peak to Peak Value
- Output Voltage Peak to Peak Value
- Efficiency
- IC Junction Temperature
- Mode
- Footprint
- BOM Cost

Then, simulate your design on “Sim” page and share the following plots. Note that the simulation type can be changed. In order to simulate, click “Start New Simulation” button and wait until it complete (it may take some time to complete).

- Output Voltage vs Time Graph **for Steady-State**
- Inductor Current vs Time Graph **for Steady-State**
- Output Voltage & Load Current vs Time **for Load Transient**
- Comment on the results.
