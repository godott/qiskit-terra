# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Pass for detecting commutativity in a circuit.

Property_set['commutation_set'] is a dictionary that describes
the commutation relations on a given wire, all the gates on a wire
are grouped into a set of gates that commute.

TODO: the current pass determines commutativity through matrix multiplication.
A rule-based analysis would be potentially faster, but more limited.
"""

from collections import defaultdict
import numpy as np
from qiskit.circuit import QuantumRegister, QuantumCircuit
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.basepasses import AnalysisPass
from qiskit.quantum_info.operators import Operator

_CUTOFF_PRECISION = 1E-10

class CommutationAnalysis(AnalysisPass):
    """An analysis pass to find commutation relations between DAG nodes."""

    def __init__(self):
        super().__init__()
        self.gates_on_wire = {}

    def run(self, dag):
        """
        Run the pass on the DAG, and write the discovered commutation relations
        into the property_set.
        """
        # Initiate the commutation set
        self.property_set['commutation_set'] = defaultdict(list)

        # Build a dictionary to keep track of the gates on each qubit
        # The key with format (wire_name) will store the lists of commutation sets
        # The key with format (node, wire_name) will store the index of the commutation set
        # on the wire with wire_name, thus, for example:
        # self.property_set['commutation_set'][wire_name][(node, wire_name)] will give the
        # commutation set that contains node.

        for wire in dag.wires:
            wire_name = "{0}[{1}]".format(str(wire[0].name), str(wire[1]))
            self.property_set['commutation_set'][wire_name] = []

        # Add edges to the dictionary for each qubit
        for node in dag.topological_op_nodes():
            for (_, _, edge_data) in dag.edges(node):

                edge_name = edge_data['name']
                self.property_set['commutation_set'][(node, edge_name)] = -1
        
        # Construct the commutation set
        for wire in dag.wires:
            wire_name = "{0}[{1}]".format(str(wire[0].name), str(wire[1]))

            for current_gate in dag.nodes_on_wire(wire):

                current_comm_set = self.property_set['commutation_set'][wire_name]
                if not current_comm_set:
                    current_comm_set.append([current_gate])

                if current_gate not in current_comm_set[-1]:
                    prev_gate = current_comm_set[-1][-1]
                    does_commute = False
                    try:
                        does_commute = _commute(dag, current_gate, prev_gate)
                    except TranspilerError:
                        pass
                    if does_commute:
                        current_comm_set[-1].append(current_gate)

                    else:
                        current_comm_set.append([current_gate])

                temp_len = len(current_comm_set)
                self.property_set['commutation_set'][(current_gate, wire_name)] = temp_len - 1

def _commute(dag, node1, node2):

    if node1.type != "op" or node2.type != "op":
        return False

    new_qreg = []

    for node in [node1, node2]:
        for wire in node.qargs:
            if wire not in new_qreg:
                new_qreg.append(wire)

    new_qr = QuantumRegister(len(new_qreg))

    circ_n1n2 = QuantumCircuit(new_qr)
    circ_n2n1 = QuantumCircuit(new_qr)

    for node in [node1, node2]:
        qarg_list = []
        for wire in node.qargs:
            qarg_list.append(new_qr[new_qreg.index(wire)])
        circ_n1n2.append(node.op, qargs=qarg_list)

    for node in [node2, node1]:
        qarg_list = []
        for wire in node.qargs:
            qarg_list.append(new_qr[new_qreg.index(wire)])
        circ_n2n1.append(node.op, qargs=qarg_list)

    if_commute = np.allclose(Operator(circ_n1n2).data, Operator(circ_n2n1).data,
                             atol=_CUTOFF_PRECISION)

    return if_commute
