# EE 463 Hardware Project

## AC to DC Motor Drive

### Deadline: TBA (After the finals)


In this project you are required to make a controlled rectifier that will be used to drive a DC Motor.

 - Input: 3 Phase, or 1 Phase AC Grid Supply
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

I believe the most sensible way of connection is shunt-excited, however you are free to use any other connections (series, compound etc) if required.

### Project Steps:

- Choose your partners: Each group will consist of 3 people. You are free to choose your partners.

- Open a public repo: Open a public repo that you will put all your work into, and send me a link.

- Decide on a topology: Discuss the advantages and disadvantages of each topology. Simulate your design in order to evaluate the performance. Don't forget about how to generate control/gate signals.

- Component Selection: Find the suitable components. Don't forget the logistics, it may take quite a lot of time to obtain some products.

- Implementation: Build a prototype as fast as possible, and keep iterating.

- Demo Day



### Hints:

Hardware implementation is quite risky. Design process and the prototyping can take a much longer time that you have anticipated. A simulation project can be straightforward, but a hardware project is like below:

![](./https://blog.sweek.com/wp-content/uploads/2015/12/5.png)

Therefore, I stongly advise you to start working immediately, and:

![](http://img.picturequotes.com/2/244/243483/fail-early-fail-often-in-order-to-succeed-sooner-quote-1.jpg)


TBA


