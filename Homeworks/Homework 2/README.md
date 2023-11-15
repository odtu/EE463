# EE 463 Homework#2

## Device Parameters

### Deadline: 26/11/2023 23:59

Please check [evaluation.md](evaluation.md) for other details and evaluation criteria about the project. Open a **private repository**, which you will put all your work into. Please add [Ogün](https://github.com/OgunAltun) as a collaborator.

**1) Diode parameters**<br />
 **a)** Define the 5 important power diode characteristics with their symbol and meanings.

[Example: I<sub>ave</sub> is the diode forward average current, defined under nominal operating conditions (say 75C if it is defined so), and it signifies...) ].<br />

**b)** Explain the losses of diodes. Which parameters affect the losses? 

**c)** Select diodes with around 1A, 10A, and 100A current ratings. (at most 5 different types/samples for each current rating, considering different speed, different voltage rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

Hint: You can search devices through Digikey, Mouser, Farnell etc. or through the webpages of manufacturers such as Infineon, Semikron, IXYS, Fairchild, International Rectifier, Microsemi, Mitsubishi, Fuji, Toshiba, ABB, ST, Cree...<br />

**d)** Select diodes with around 5V, 50V, and 500V voltage ratings. (at most 5 different types/samples for each voltage rating, considering different speed, different current rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**e)** By referencing the selected diodes in part 1.c and 1.d, comment on the trade-offs of the diode parameters in detail. How does other parameters change when voltage and current ratings are increased? What may be the advantages and/or disadvantages of choosing an overdesign diode -for example, choosing a diode with 100A current rating to a design with a 20A current? Explain in detail.

[Example: Select two diodes with same voltage and different current ratings. Put these two in a small table and compare the effect of varying voltage on other diode parameters.]

**2) MOSFET parameters**<br />

**a)** Define the 5 most important power MOSFET characteristics with their symbol and meanings.

**b)** Explain the losses of MOSFETs. Which parameters affect the losses? 

**c)** Select MOSFETs with around 1A, 10A, and 100A current ratings. (at most 5 different types/samples for each current rating, different voltage rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**d)** Select MOSFETs with around 5V, 50V, and 500V voltage ratings. (at most 5 different types/samples for each voltage rating, considering different current rating, different material type, i.e., Si, SiC, etc.). Put them into a table to compare the change in most important parameters.

**e)** By referencing the selected MOSFETs in part 2.c and 2.d, comment on the trade-offs of the MOSFET parameters in detail. How does other parameters change when voltage and current ratings are increased? What may be the advantages and/or disadvantages of choosing an overdesign MOSFET? Explain in detail.

**3) Simulation**<br />

Select two different diodes and MOSFETs with different ratings. Find the spice models of the components and simulate them in LTspice. Show the losses of semiconductors and compare the results. (Hint: You can use below circuit to examine losses. To compare losses of diodes, keep the MOSFET same for two different diode selection and vice versa.) 

![](Loss.png)

**4) Wide-bandgap semiconductors**<br />

Find a commercial product which contains SiC and/or GaN semiconductor devices. Explain the advantages/disadvantages of using wide-bandgap semiconductors based on your selected product.
