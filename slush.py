#!/usr/bin/env python3

import enum
import random

#  C  set of correct nodes      c  number of correct nodes
#  B  set of byzantine node     b  number of byzantine nodes
#  N  set of all nodes          n  number of nodes

num_rounds = 100    # m in the whitepaper
num_nodes = 100     # n in the whitepaper
sample_size = 5     # k in the whitepaper
threshold = 0.6     # α in the whitepaper

class Color(enum.Enum):
    UNCOLORED = 0
    RED = 1
    BLUE = 2


class Node:
    def __init__(self):
        self.color = Color.UNCOLORED

    def on_query(self, color):
        if self.color == Color.UNCOLORED:
            self.color = color
        return self.color

    def accept(self):
        return self.color

# FIXME The whitepaper says "a node starts out initially in an uncolored
#       state", but the pseudocode in Figure 1 implies the initial color can
#       be any color

def slush_loop(node, initial_color):
    node.color = intial_color
    for round in range(num_rounds):
        if node.color == Color.UNCOLORED:
            continue

        contacts = random.sample(nodes.difference({node}), sample_size)
        responses = [contact.on_query(node.color) for contact in contacts]

        for color in [Color.RED, Color.BLUE]:
            if reponses.count(color) > threshold * sample_size:
                node.color = color
    node.accept()
