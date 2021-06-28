# Incrementally Predictive RV

A Python tool to generate incrementally predictive monitors. Given a XES file representing previous executions of the system, an LTL property to verify and a trace of events denoting the current system execution, the tool synthesises and runs a predictive monitor to conclude the satisfaction (resp. violation) of the LTL property w.r.t. the current system execution.

## How to install

- Install https://github.com/AngeloFerrando/MultiModelPredictiveRuntimeVerification
- Install https://pm4py.fit.fraunhofer.de/

## How to use

To run the tool

```bash
-$ python main.py <path_to_XES_file> <LTL_property> <path_to_trace_file> <path_to_multimodeprv> --threshold <threshold_value> --view
```

where:
- <path_to_XES_file> is the path to the XES file containing the event logs of previous system executions
- <LTL_property> is the LTL property to verify at runtime
- <path_to_trace_file> is the path to the file containing the current execution trace (the one to verify at runtime with the monitor)
- <path_to_multimodeprv> is the path to the folder where MultiModelPredictiveRuntimeVerification has been saved (first point in How to install)
- <threshold_value> is the value used to prune transitions which are unlikely (according to the chosen threshold), its default value is 0.0
- if -- view is present, the tool also generates svg pictures in the folder for the DFG extracted through Process Mining and its corresponding Buchi Automaton

## Try an example

To run the tool on the example (change <path_to_multimodeprv> with the correct path on your machine)

```bash
-$ python main.py ./running-example.xes 'F(check_ticket) | F(examine_casually)' ./trace.txt <path_to_multimodeprv> --threshold 0.05 --view
```

The tool should print some information about the different phases of the algorithm (from DFG extraction to Monitor synthesis), and it should end with a RES: TRUE. Which means the LTL property has been verified by the current system execution reported in ./trace.txt.
