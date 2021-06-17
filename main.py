import os
import sys
from pm4py.objects.log.importer.xes import importer as xes_importer
import pandas as pd
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
import argparse
sys.path.insert(0,'/usr/local/lib/python3.7/site-packages/')
import spot

class MarkovDecisionProcess:
    def __init__(self, initial_state, states, transitions):
        self.__initial_state = initial_state
        self.__states = states
        self.__transitions = transitions
    def to_hoa(self, threshold = 0.0):
        events = []
        map_evs = {}
        id = 0
        for t in self.__transitions:
            for ev in self.__transitions[t]:
                if '"' + ev.replace(' ', '_') + '"' not in events:
                    events.append('"' + ev.replace(' ', '_') + '"')
                    # if ev != self.__initial_state:
                    map_evs[ev] = id
                    id += 1
        res = '''HOA: v1
States: {n_states}
Start: 0
AP: {n_evs} {evs}
acc-name: Buchi
Acceptance: 1 Inf(0)
--BODY--
'''.format(n_states = len(self.__states), n_evs = len(events), evs = str.join(' ', events))
        my_map = {}
        my_map[self.__initial_state] = 0
        id = 1
        for s in self.__states:
            if s not in my_map:
                my_map[s] = id
                id = id + 1
        for s in self.__states:
            res += 'State: ' + str(my_map[s]) + ' {0}\n'
            for ev in self.__transitions[s]:
                if self.__transitions[s][ev][1] >= threshold:
                    res += '[' + str.join('&', [str(map_evs[ev]) if i == map_evs[ev] else ('!' + str(i)) for i in range(0, len(events))]) + '] ' + str(my_map[self.__transitions[s][ev][0]]) + '\n'
        res += '--END--'
        return res

def main(argv):
    parser = argparse.ArgumentParser(
        description='Python prototype of Incrementally Predictive RV',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('log',
        help='log file to derive the model of the system',
        type=str)
    parser.add_argument('formula',
        help='LTL formula to verify',
        type=str)
    parser.add_argument('trace',
        help='the trace to analyse',
        type=str
    )
    parser.add_argument('path_to_monitor',
        help='the path to the monitor script',
        type=str
    )
    parser.add_argument('--threshold',
        help='the minimum probability to consider in the Buchi generation (default: 0.0)',
        type=float
    )
    parser.add_argument('--view', action='store_true')
    args = parser.parse_args()
    log = xes_importer.apply(args.log)

    dfg = dfg_discovery.apply(log)

    if args.view:
        from pm4py.visualization.dfg import visualizer as dfg_visualization
        parameters = {dfg_visualization.Variants.PERFORMANCE.value.Parameters.FORMAT: 'svg'}
        gviz = dfg_visualization.apply(dfg, log=log, variant=dfg_visualization.Variants.FREQUENCY, parameters=parameters)
        dfg_visualization.save(gviz, 'dfg.svg')

    ALPHABET = set()
    for s in dfg:
        ALPHABET.add(s[0])
        ALPHABET.add(s[1])
    print(dfg)
    dfg_initial_states = set()
    for ev in ALPHABET:
        counter_out = 0
        counter_in = 0
        for t in dfg:
            if t[0] == ev:
                counter_out = counter_out + dfg[t]
            if t[1] == ev:
                counter_in = counter_in + dfg[t]
        if counter_out > counter_in:
            dfg_initial_states.add((ev, counter_out - counter_in))
    mdp_initial_states = None
    mdp_states = set()
    mdp_transitions = {}
    drg_initial_states_copy = dfg_initial_states.copy()
    while dfg_initial_states:
        s_tuple = dfg_initial_states.pop()
        if s_tuple[0] in mdp_states:
            continue
        s = s_tuple[0]
        s_c = s_tuple[1]
        if s_tuple in drg_initial_states_copy:
            if 'init' not in mdp_states:
                mdp_states.add('init')
                mdp_initial_states = 'init'
                mdp_transitions['init'] = {}
            mdp_transitions['init'][s] = (s, s_c)
        for t in dfg:
            if t[0] == s:
                mdp_states.add(s)
                if s not in mdp_transitions:
                    mdp_transitions[s] = {}
                mdp_transitions[s][t[1]] = (t[1], dfg[t])
                insert = True
                for aux in dfg_initial_states:
                    if aux[0] == t[1]:
                        insert = False
                        break
                if insert:
                    dfg_initial_states.add((t[1], 0))
    for t in mdp_transitions:
        for ev in mdp_transitions[t]:
            if mdp_transitions[t][ev][0] not in mdp_states:
                mdp_states.add(mdp_transitions[t][ev][0])
    mdp_states_aux = set()
    id = 0
    my_map = {}
    mdp_transitions_aux = {}
    for s in mdp_states:
        mdp_states_aux.add('s_' + str(id))
        my_map[s] = 's_' + str(id)
        id = id + 1
    mdp_initial_states = my_map['init']
    for s in mdp_states:
        if my_map[s] not in mdp_transitions_aux:
            mdp_transitions_aux[my_map[s]] = {}
        if s in mdp_transitions:
            for ev in mdp_transitions[s]:
                mdp_transitions_aux[my_map[s]][ev] = (my_map[mdp_transitions[s][ev][0]], mdp_transitions[s][ev][1])
    mdp_states = mdp_states_aux
    mdp_transitions = mdp_transitions_aux
    for s in mdp_states:
        for ev in ALPHABET:
            if ev not in mdp_transitions[s]:
                mdp_transitions[s][ev] = (s, 0)
    for s in mdp_states:
        sum = 0
        for t in mdp_transitions[s]:
            sum = sum + mdp_transitions[s][t][1]
        if sum == 0:
            continue
        for t in mdp_transitions[s]:
            mdp_transitions[s][t] = (mdp_transitions[s][t][0], mdp_transitions[s][t][1] / sum)
    mdp = MarkovDecisionProcess(mdp_initial_states, mdp_states, mdp_transitions)
    with open('model.hoa', 'w') as file:
        if args.threshold:
            file.write(mdp.to_hoa(args.threshold))
        else:
            file.write(mdp.to_hoa())
    if args.view:
        with open('model.svg', 'w') as file:
            file.write(spot.automaton('model.hoa').show('.st').data)
    res = os.popen('python3 {path}/monitor.py \'{phi}\' {trace} --models {m} --centralised'.format(phi=args.formula, trace=args.trace, m='./model.hoa', path=args.path_to_monitor)).read()
    print(res)
if __name__ == '__main__':
    main(sys.argv)
