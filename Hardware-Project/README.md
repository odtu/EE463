# EE 463 Hardware Project

## AC to DC Motor Drive 

### Deadline: TBA (After 16th of January)

In this project you are required to make a controlled rectifier that will be used to drive a DC Motor.

 - Power Input: 3 Phase, or 1 Phase AC Grid
 - Output: Adjustable DC Output

You are free to choose any topology such as (but not limited to):

 - 3-Phase Thyristor Rectifier
 - 1-Phase Thyristor Rectifier
 - Diode Rectifier + Buck Converter

### Specs:

You are required to drive the following motor-generator sets:

![](./motor-set.jpg)

![](./motor-label.jpg)

We measured the motor's parameters as follows:

 - Armature Winding: 28 Ω, 13.3 mH
 - Series Winding: 65 mΩ, 260 uH
 - Shunt Winding: 8.26 kΩ, 6.4 H
 - [Interpoles](https://www.quora.com/Electrical-Machines-What-do-interpoles-do-in-DC-motors) Winding: 0.8 Ω, 5.8 mH
 - Inertia: TBA

I believe the most sensible way of connection is shunt-excited, however you are free to use any other connections (series, compound etc) if required.

### Project Steps:

- Choose your partners: Each group will consist of 3 people. You are free to choose your partners.

- Create a public repo: Open a public repo, which you will put all your work into. Please add [me](https://github.com/ozank) and [İlker](https://github.com/ilkersahin78) as a collaborator.

- Topology Selection: Discuss the advantages and disadvantages of each topology, and decide on a topology. You are required prepare a document to support your decision.

- Computer Simulations: According the your topology selection, you are going to run computer simulations, to prove the performance characteristics of your drive. It is best to simulate as detailed as possible to catch possible hardware problems (for example, how to generate control/gate signals).

- Component Selection: According to your analytical calculations and computer simulations decide on which components you are going to use. Not only choose the power components, but also decide on the control, and axillary components. Don't forget to plan logistics, it may take weeks to get some components.

- Implementation: Build a prototype as fast as possible, and keep iterating.

- Demo Day: In the demo day, you are expected to present your working prototypes. You are required to start the DC motor from standstill to rated speed under no load (but still you have the inertia, and the friction) and run for 2 minutes. You are allowed to soft start your drive (i.e for charging capacitors etc) with a variac, but variac should not be used to control the voltage while the motor is running.

### Grading

Project Outcomes:

- Design Report (40 pts): A report that presents your design decisions, computer simulations, and component selection. Similar grading rules apply with previous projects (i.e. format, number of commits etc.)

- Test Results (15 pts): This section can be added in to the design report, or submitted as a separate report. It should contain your results with the motor running (data can be collected on the demo day, but preferably earlier) The report can contain any other useful tests (i.e. functionality of the switches, tests with R load etc.)  

- Video (15 pts): A video telling your story during the design process and project implementation. It is also expected to put a demo of the working prototype. Videos of max. 3 min should be uploaded to YouTube (or any other online video hosting website). Each team member should appear in the video.

- Demo Day (30 pts): Each team is expected to present their prototype in the demo day. If you have a prototype, but somehow if it doesn't work on the demo day, you will get zero points from this part. However, if you don't come up with a prototype, or convince me that you put enough effort in building a prototype, you will get zero points from the all hardware project (yes, even if you had the design report).

#### Bonus Parts

You can get extra points (25 pts for each) in any of the following:

- Industrial Design Bonus: Implement your design in a PCB, enclose it in a plastic/metal box and label input/outputs with proper connections for safe operation.

- Robust Design Bonus: Your design should withstand a test of 10 min under full-load (i.e. 2.8 kW). Normally you are just required to run the motor at rated speed at no-load.

- Feedback Bonus: Implement a speed  regulator to keep the speed constant even if the the load is varied.

- Best Grid Interface Bonus: THD on the grid side will be measured at the demo day (under full load), and this bonus is awarded to the project with the lowest THD.

- Four-Quadrant Bonus: Normally you are required to make a single quadrant DC motor drive, but implement a four-quadrant drive to get this bonus.

- Best Video Bonus: Just get creative, and try to get a fun and informative video to describe your project progress.


### Teams:
Teams I am aware so far:

- [Kesla Motors: Melisa, Hande, Özgür](https://github.com/ghandeb/KESLA-Motors)
- [Hakan S, Ceren, Yusuf](https://github.com/hakansrc/EE463-Hardware-Project)
- [Ripple Warriors: Eralp, Raşit, Mahmut Enes](https://github.com/MehmetEralpKose/Ripple-Warriors-Hardware-Project-)
- [EMAchines: Ümit Mert, Ekin, Asım](https://github.com/UmitMertCaglar/EE463-Hardware-Project)
- [Caner, Uğur, Tuna](https://github.com/caneryagci/EE_463-Hardware-Project)
- [Dank Drivers: Mert, Hakan Polat](https://github.com/hakanpolat/EE463--Dank-Drivers)
- [Ankara Instruments: Emin, Özgür, Talgat](https://github.com/emincinalioglu/Ankara-Instruments)

If your name is not listed above, please inform me asap.

### Frequently Asked Questions

- Can I use the lab before demo day?

Yes, you will be able to use both the Machinery Lab, and Machinery lab, but only after all the lab sessions are finished (i.e. after 1st of January)

- What equipment will be available for us in the lab?

You will be able to use, osciloscope, power supply, soldering station, function generator, variacs.

- Can I also work at nights in the lab?

Unfortunately, due to safety regulations, you have to work under technician supervision. Only exception is if an assistant already working in the lab after-hours, you can use the lab, but there is no fixed schedule for that.


### Hints:

Hardware implementation is quite risky. Design process and the prototyping can take a much longer time that you have anticipated. A simulation project can be straightforward, but a hardware project is like below:

![](https://blog.sweek.com/wp-content/uploads/2015/12/5.png)

Therefore, I strongly advise you to start working immediately, and:

![](http://img.picturequotes.com/2/244/243483/fail-early-fail-often-in-order-to-succeed-sooner-quote-1.jpg)


