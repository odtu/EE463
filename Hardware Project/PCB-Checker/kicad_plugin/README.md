# EE463 PCB Check: KiCad plugin

A button in the KiCad PCB editor that checks your board and shows the result in your browser. Works with KiCad 8, 9 and 10.

## Install (once)

In the `PowerLabPCBChecker` folder, run:

```bash
"C:\Program Files\KiCad\10.0\bin\python.exe" install_plugin.py
```

Then in the PCB editor choose **Tools → External Plugins → Refresh Plugins**. The green **EE463 PCB Check** button appears in the top toolbar.

## Use

1. Open your board in the PCB editor.
2. Click **EE463 PCB Check**.
3. Wait up to a minute. The report opens in your browser.

The report is also saved next to your board as `<board>_check.html`.

## Read the report

- **Red (must fix):** the board can't be made or will fail.
- **Orange (should fix):** fix it, or be ready to explain why.
- **Blue (check):** look at it yourself.

Click a problem to see where it is on the board.

## Problems

- **No button:** restart KiCad.
- **"Save the board first":** save the board once, then click again.
- **Wrong parts or nets found:** run *Tools → Update PCB from Schematic (F8)* and check again.

To check your Gerber files, use `check_pcb.bat` instead (see the main README).
