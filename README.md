# AI Memory Leak Detector

This project is a desktop dashboard for memory leak and resource anomaly detection.
Python is used for the UI, graph, and OS resource connection.
Python uses a real `IsolationForest` model for anomaly detection.
C is used for the final leak warning rules.

## Project structure

```text
final_project/
|-- c_core/
|   |-- build.ps1
|   `-- monitor_core.c
|-- memory_leak_detector/
|   |-- __init__.py
|   |-- app.py
|   `-- monitor.py
|-- main.py
|-- requirements.txt
`-- README.md
```

## What it does

- shows 4 dashboard cards
- lets you set a memory threshold
- reads live OS memory and CPU values with `psutil`
- runs an `IsolationForest` model on memory and CPU history
- sends the model score and system data to C for final leak scoring
- plots memory and CPU on a live graph
- exports warning logs to CSV
- shows `System Stable` or `System Warning`

## How leak risk is detected

Python reads live OS memory and CPU values with `psutil`.
Python fits an `IsolationForest` model on the recent history window.
The model score and latest system values are sent to `c_core/monitor_core.c`.

The C core adds simple final rules when:

- memory usage crosses the selected threshold
- total OS memory reaches 85% or more
- CPU reaches 90% or more

A leak warning is shown when the score is 60 or more, or when memory usage is above the threshold.

## Build the C core

```powershell
cd c_core
powershell -ExecutionPolicy Bypass -File .\build.ps1
cd ..
```

## Run the project

```powershell
pip install -r requirements.txt
python main.py
```

Write a threshold value in the box, then press `Start`.
