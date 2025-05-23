# Decay computation

## Purpose

This project computes the **End Of Beam (EOB)** individual activity of a mix of isotopes produced by a cyclotron.

## Usage

### 1. Data Input

Record the measured activity at different times after the end of production (**EOB : t = 0 min**).  
Enter your data in the Excel file: **`decay.xlsx`**.  
You can input as many values as you like (more than 7 is recommended).

![Data input example](images/readme_pic_1.jpg)

---

### 2. Isotope Selection

The program attempts to identify contributing isotopes from a predefined list of common isotopes.  
You can customize the list directly in **`decay.xlsx`** by checking/unchecking boxes or adding new isotopes (make sure to follow the existing syntax).

![Isotope selection example](images/readme_pic_2.jpg)

---

### 3. Computation Algorithm

The algorithm iteratively finds the most fitting solution. If negative activity values are found, they are removed one by one.  
Each iteration is logged in **`result.txt`**.

![Iteration log example](images/readme_pic_3.jpg)

---

### 4. Final Results

The program computes the theoretical decay curves of the final isotopes and compares them with the measured values.  
Final results are displayed on a local webpage at:

http://localhost:127.0.0.1:56146/

![Final result example](images/readme_pic_4.jpg)

---

## Execution

You can run the program using:

- The Windows executable: **`decay.exe`**
- Or the Python source code: **`decay.py`**

---

## Feedback

If you encounter incorrect results or have suggestions for improvement, feel free to contact me.