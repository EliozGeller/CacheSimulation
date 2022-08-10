## Introduction

This work is done in join with Nvidia (Mellanox) and aims to check various caching algorithms 
in high-speed networks that operate in a controller-switch architecture.

## Install PyTricia
This project uses a data structure that need to be installed separetly and can be found in:
https://github.com/jsommers/pytricia

## Structure
The project contains two main parts:
 * Traffic Generator - Consist of the folders:
   * TrafficGenerator - The main classes and structure that uses to generate the code
   * TGDriverCode - The code that generates and analyze the traffic from the TrafficGenerator structure files
   * data - Hold CDF of flow sized that is common in data centers and is used to determine the distribution of 
   the flow sizes when generating traffic.
 * Simulator
   * All the code in this folder is used by the simulator, and the main file is in ``Simulator.py``
   * The structure files are in:
     * Simulator architecture files are in: ``Algorithm.py`` ``Switch.py`` ``Controller.py``
     * Simulator auxiliary files are in: ``Policy.py``,``TimeSeriesLogger.py``,``SimulatorIO.py``
   * After defining the configurations and generating the desired trace, you can use the ``packet_trace.json``
   as an input to the simulator.
