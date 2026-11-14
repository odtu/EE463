# EE463 PCB Checker

Checks your **EE463 DC–DC converter** board before you send it to the fab, and shows the result in your browser. It works offline and needs only KiCad (8, 9 or 10).

## How to use

**Check your KiCad board or your submission zip (Windows):**
drag your `.kicad_pcb` file, project folder or submission `.zip` onto **`check_pcb.bat`**.

**Check inside KiCad:** install the button once. See [kicad_plugin/README.md](kicad_plugin/README.md).

**Command line (any system):**

```bash
python check_pcb.py MyBoard.kicad_pcb --open
```

Add `--overload` to check for the 7.5 A bonus.

Before you submit, run it on **the zip you will send**. It also checks that the Gerbers, drill files, schematic, PCB file and BOM are all there.

## What it checks

- **Manufacturing (PCBWay standard price):** track width, spacing, holes, copper near the edge, board outline, layers.
- **Power stage:** track width for 5 A, spacing for 48 V, capacitor voltage ratings, the input capacitor at the switches, the gate driver close to the MOSFETs, feedback routing, nothing routed under the inductor.
- **Testing:** test points on ground, gate signals and supplies; parts big enough to solder by hand.
- **KiCad DRC.**

If you use another EDA tool, only the manufacturing checks run, from your Gerber files.

## Reading the report

- **Red (must fix):** the board can't be made or will fail.
- **Orange (should fix):** fix it, or be ready to explain why.
- **Blue (check):** look at it yourself.

At the top, check that **"What the checker found on your board"** is right (input, switch node, output). Click a problem to see where it is on the board. At the end, go through **"Check these yourself"**.

## Example

`examples/demo_buck` is a small buck converter with mistakes in it on purpose. Run the checker on it to see a report.

## Contact

Questions or problems: [wa.me/ekremturanfirat](https://wa.me/ekremturanfirat)
