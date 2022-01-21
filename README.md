# Qiskit Trebugger  <img src = 'https://user-images.githubusercontent.com/57539040/144383032-6a0da7cf-d03a-4469-9be6-a3da39a2f727.png' align = "center" height = "40px" width = "40px">


A new take on debuggers for quantum transpilers. 
This repository presents a debugger for the **qiskit transpiler** in the form of a light weight jupyter widget. Built as a project for the Qiskit Advocate Mentorship Program, Fall 2021. 

<img src = 'https://user-images.githubusercontent.com/57539040/145200175-8b277d91-22eb-40c9-bbbd-c6e0ac2de4e1.gif' width = '90%' height = '44%'>

## Installation
1. To install the debugger using pip (a python package manager), use - 

```bash
pip install -i https://test.pypi.org/simple/ --extra-index https://pypi.org/simple/ qiskit-trebugger
``` 
- PIP will handle the dependencies required for the package automatically and would install the latest version. 
- Currently the project is hosted as a test package and would be hosted on the real index when *tests* are added.


2. To directly install via github follow the steps below after using `git clone`: 
 ```bash
 git clone https://github.com/TheGupta2012/qiskit-timeline-debugger.git
 ```
  - Make sure `python3` and `pip` are installed in your system
  - Use `pip install -r requirements` to install the debugger dependencies
  - Note : with this method, you can only use the debugger in the installed directory

## Usage Instructions

- After installing the package, import the `Debugger` instance from `qiskit_trebugger` package. 
- To run the debugger, simply replace the call to `transpile()` method of the qiskit module with `debug()` method of your debugger instance. For an example - 

```python
from qiskit import QuantumCircuit
from qiskit.test.mock import FakeCasablanca
from qiskit_trebugger import Debugger

debugger = Debugger()
backend = FakeCasablanca()
circuit = QuantumCircuit(3)
circuit.h(0)
circuit.cx(0,1)
circuit.cx(1,2)
circuit.measure_all()
# replace transpile call 
debugger.debug(circuit, backend = backend)
``` 
- On calling the debug method, a new jupyter widget is displayed providing a complete summary and details of the transpilation process for circuits of < 2000 depth
- With an easy to use and responsive interface, users can quickly see which transpiler passes ran when, how they changed the quantum circuit and what exactly changed.


## Feature Highlights

### 1. Circuit Evolution
- See your circuit changing while going through the transpilation process for a target quantum processor.
- A new custom feature enabling **visual diffs** for quantum circuits, allows you to see what exactly changed in your circuit using the matplotlib drawer of the qiskit module.

> Example 
- Circuit 1
<img src='https://user-images.githubusercontent.com/57539040/145244617-bb800baa-ec28-4024-9d0b-9073294e97a5.png' height = "20%" width = "47%">

- Circuit 2
<img src='https://user-images.githubusercontent.com/57539040/145244998-d73792df-e66d-422b-94c1-8b4d9a985e26.png' height = "40%" width = "70%">



### 2. Circuit statistics
- Allows users to quickly scan through how the major properties of a circuit transform during each transpilation pass. 
- Helps to quickly isolate the passes which were responsible for the major changes in the resultant circuit.

<img src = 'https://user-images.githubusercontent.com/57539040/144386786-98db4435-8c31-4257-9529-7e4d8b10309c.png' width = '75%' height = '15%'>

### 3. Transpiler Logs and Property sets
- Easily parse actions of the transpiler with logs emitted by each of its constituent passes and changes to the property set during transpilation
- Every log record is color coded according to the level of severity i.e. `DEBUG`, `INFO`, `WARNING` and `CRITICAL`.


<img src = 'https://user-images.githubusercontent.com/57539040/144387552-17aa6229-c4ba-439f-9a72-3aefed52ec4f.png' height = '38%' width = '55%'>



## Demo Video 
- Please follow [this](to be added) link for a demonstration of our project.

## Contributors 
- [Aboulkhair Foda](https://github.com/EgrettaThula)
- [Harshit Gupta](https://github.com/TheGupta2012)




