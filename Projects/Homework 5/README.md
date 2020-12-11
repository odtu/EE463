# EE 463 Homework#5

## Understanding Power

### Deadline: 20/12/2020 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add Tokgöz(/tokgozfurkan) and Karakaya(/furkankarakaya) as a collaborator.

**1) Active Power Creation**<br />
 **a)** Let's say you have a voltage source supplying a current such as

 ![](Equation.png)<br />


Calculate the supplied active power of this voltage source. Indicate the components creating active power.

*Even though having clear steps is important, you do not need to show each step in calculations. You can be direct reasonably.*

*Writing the equations in an equation editor such as Word Equation, Latex Equation etc. is a must.*

**b)** What is the rule of thumb to create a nonzero active power?



**2) Understanding Active and Reactive Power**<br />

You have the following circuit where the load resistance is 15-ohms and thyristor can be considered as ideal.

![](OPCR.jpg)<br />
  *Suggestion: You can use TemplateForQ2.slx file for the simulations*

**a)** Apply a gate signal synchronized with your voltage supply, i.e., non-delayed pulses. Using power measurement block (Simscape / Power Systems / Simscape Components / Control / Measurements), find supplied or consumed active and reactive power of source and load. Give active power of supply & load in a table up to 9th harmonic.

  *i)* Is active power conserved harmonicwise, why?<br />
  *ii)* Is reactive power conserved from source to load?

**b)** Apply a gate signal with 7 ms delay using Transport Delay block. Please give the active and reactive power tables up to 9th harmonic for any component that you comment on.

  *i)* Is active power conserved? <br />
  *ii)* Is reactive power conserved from source to load? Explain the difference from the part (ii) of (a). <br />
  *iii)* Is reactive power conserved harmonicwise in a circuit? <br />
  *iv)* Is apparent power conserved from source to load? <br />
  *v)* Is power factor conserved from source to load? <br />

**c)** Change the load with an R-L load where resistance is 15-ohms and inductance is 12 mH. Give the active and reactive power tables up to 9th harmonic for supply and load.

*i)*  What is the power factor of the supply?<br />
*ii)* Calculate the load power factor using the load parameters. Does it match with the simulation result? What are the displacement power factor and harmonic power factor of the load?<br />

**3) Feedback (Bonus)**<br />

How much time did you spend for this homework?
