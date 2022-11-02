# Hardware Project Tips

**REMEMBER ALWAYS SAFETY FIRST!**

Hardware implementation is quite risky. Design process and the prototyping can take a much longer time that you have anticipated. A simulation project can be straightforward, but a hardware project is like below:

![](https://blog.sweek.com/wp-content/uploads/2015/12/5.png)

Therefore, I strongly advise you to start working immediately, and:

![](http://img.picturequotes.com/2/244/243483/fail-early-fail-often-in-order-to-succeed-sooner-quote-1.jpg)

Here's a few tips for you. Please remember all of these items are based on real experiences. Please consider each of them.

----

# DO

- Start thinking about your hardware project early. Fail early, fail often, in order to succeed sooner.
- Consider and understand your project requirements in detail.
- Model your topology with all possible non-idealities.
- Discuss your ideas and findings with your friends and share them.
- Look for design notes and guides, instead of articles (for now).
- According to your simulation results, choose semiconductor devices wisely, with safety
margin.
- Choose capacitance, resistance and inductance values that are commercially available.
- Capacitor selection bottleneck: Voltage ripple (also current ripple)
- Inductor selection bottleneck: Max. Current, current ripple
- If you need a large inductor that is not available in shops, build your own. We have [cores](https://github.com/odtu/ee463/blob/master/Hardware-Project/components.md) that is available for your usage.
- Buy spare components. You don’t want to visit Konya Sokak 3 times a day. (☹)
- Let your friends know when you go shopping to Konya Sokak.
- Do not use jumpers unless it is really necessary.
- Isolate your controller.
- Identify high current loops, keep them short and thick.
- Place gate driver as close as possible to the gate leg of the transistor.
- Keep your circuit neat and easy to debug.
- Use stranded cables.
- Twist your cables.
- Use fuses.
- Start experimenting with low voltage and current, increment it gradually.
- Specify measurement points considering earth and floating ground connections.

# DON'T

- Don’t hesitate to share what you know, recognize or find. (Don’t be an typical EE student. No
one is your enemy or opponent.)
- Don’t procrastinate the project.
- Don’t apply a step voltage to the motor.
- Don’t connect multiple semiconductor devices on the same heat-sink without electrical
isolation.
- Don’t start your design with high frequency.
- Don’t put the soldering iron on the components for long duration, but make sure that it is hot enough.

# Useful Tips

- Motor is a big RL load, (a low pass filter) you won’t need a large LC filter.
- Optocoupler recommendation: TLP250, HCPL3120, HCPL3150
- Design your circuit (or PCB) with connectors and make sure it can be connected and disconnected from the supply and oscilloscope in a short time.
- Online shop recommendation: [direnc.net](https://www.direnc.net/), [ozdisan.com](ozdisan.com/), [Ekom Elektronik (Digikey
distributor)](https://www.e-kom.com/)  
- Local shops: Yıldırım Elektronik, Ser Elektronik, Konya Sokak
