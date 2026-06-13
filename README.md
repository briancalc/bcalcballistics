# Bcalc External Ballistics Calculator

## Readme Contents

1. What is this?
2. Who is this for?
3. Who isn't this for?
4. Installation Guide
5. User Guide
6. Credits

---

## 1. What is this?

The Bcalc External Ballistics Calculator is an open-source external ballistics calculator that returns practical trajectory data without relying on cloud-based services or subscriptions.

You can enter specific ammunition and environmental factors for up to three rounds.

The calculator then produces, across multiple specified ranges:

- output tables for trajectory metrics such as drop, wind drift, moa correction, moa wind, and velocity
- three graphs comparing drop, velocity, and kinetic energy
- text files containing all calculated metrics for integer ranges 1 to 800 yards

An internet connection is not required once installed. No user data is collected or transmitted.

## 2. Who is this for?

Hunters and hobbyists. The calculator provides ballistics data for typical field and range scenarios with the ability to compare up to 3 rounds against one another.

## 3. Who isn't this for?

Long-range precision shooters. While the calculator returns good estimates for hunting and general recreation, it lacks the advanced modeling required for true long-range precision. Check out Hornady's excellent 4DOF calculator if you are new to or considering long-range precision shooting.

## 4. Basic Linux Installation Guide

### 1. Install System Dependencies

- OpenMandriva: sudo dnf install python3 python3-pip tkinter
- Vendefoul Wolf: sudo apt install python3 python3-pip python3-tk python3-venv

### 2. Create and Activate Python Virtual Environment

- mkdir -p ~/projects/bcalc
- cd ~/projects/bcalc
- python3 -m venv bcalcext
- source bcalcext/bin/activate

### 3. Install Python Packages

- pip install -r requirements.txt

### 4. Download the Files

- download the calculator files and place them in ~/projects/bcalc (all .py, .csv, .png, .desktop files)

### 5. Run the Calculator

- from the activated bcalcext environment: python3 startprogram.py

### Optional: Launch Icon

1. Copy to applications folder:
   - cp bcalcext.desktop ~/.local/share/applications/

2. Copy icon:
   - mkdir -p ~/.local/share/icons
   - cp bcalcexticon.png ~/.local/share/icons/

3. Refresh desktop menu: search "Bcalc Ext Ballistics" in your app menu (should see the quail image)

## 5. User Guide

**Step 1:** The first step is to enter your round data by selecting a cartridge from the drop-down menu; either one of the available MFG rounds or a User Defined round. The MFG rounds will populate the drag function, the ballistic coefficient, weight, and muzzle velocity if known. Always confirm the data and you can change the values if wished. Revise the additional input parameters as required.

![Step 1](screenshots/step%205.1%20enter%20data.png)

**Step 2:** Press the "Add Round Data" button after each cartridge data is entered to store the information. Up to 3 rounds can be compared.

![Step 2](screenshots/step%205.2%20add%20round%20data.png)

**Step 3:** Press the "Run Ballistics" button to kick off the calculator.

**Step 4:** The results screen should open. Use the drop-down menus to select different ranges for the Trajectory Data section as well as the 3 graphs.

![Step 4](screenshots/step%205.4%20output%20results.png)

**Step 5:** A screenshot of the results window plus text files (1 for each round) containing the Trajectory Data for the total 800 yards can be saved to your Documents folder. Click on the blue hamburger menu at bottom left of the screen and select "Save Results."

<img src="screenshots/step%205.5a%20save%20results.png" width="350">

**Step 5 (Confirmation):** The save confirmation dialog appears.

![Step 5 Confirmation](screenshots/step%205.5b%20save%20confirmation.png)
<br><br>

**Step 6:** From the blue hamburger menu, select "Enter New Data" to return to the entry form or "Exit Program" to close.

## 6. Credits

I'm neither an external ballistics expert nor software developer. The goals for me were to learn more about bullet trajectory (we are getting there) and learn python (slow going). The calculator is offered for educational and entertainment purposes.

The Bcalc External Ballistics Calculator was created by Brian Calc.

This calculator draws heavily from the GNU Ballistics Calculator created by Derek Yates, updated by William Grim, and ported to python by Brad Rise.

In brief:

- created GUI Data Entry Form
- added MFG ammunition data
- included ability to compare rounds
- revised several ballistic formulas
- created GUI Results Screen

Plan is to continue to refine the calculator, polish the output, and cleanup the code. Suggestions for improvements are welcome.
