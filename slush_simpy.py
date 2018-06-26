#!/usr/bin/env python3

import enum
import random

import simpy


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
    def __init__(self, env, color=Color.UNCOLORED):
        self.env = env
        self.color = color

    def on_query(self, color):
        if self.color == Color.UNCOLORED:
            self.color = color
        return self.color

    def accept(self):
        return self.color

    def run(self, nodes, sample_size):
        while True:
            if self.color == Color.UNCOLORED:
                yield self.env.timeout(1)
                continue
            contacts = random.sample(set(nodes).difference({self}), sample_size)
            replies = [contact.on_query(self.color) for contact in contacts]

            for color in [Color.RED, Color.BLUE]:
                if replies.count(color) > threshold * sample_size:
                    self.color = color
            yield self.env.timeout(1)

def monitor(env, nodes):
    # TODO Overwriting only works when the output fits on a single line
    # TODO Does this run at the end of a step? beginning? indeterminate?
    while True:
        print(f'{env.now:3d}', end=' ')
        print(''.join(f'{node.color.value:d}' for node in nodes), end='\r')
        yield env.timeout(1)


if __name__ == '__main__':
    env = simpy.rt.RealtimeEnvironment()
    initial_colors = [Color(random.randint(0, 2)) for i in range(num_nodes)]
    nodes = [Node(env, color) for color in initial_colors]
    print('BEGIN')
    print(''.join('%i' % node.color.value for node in nodes))
    procs = [env.process(node.run(nodes, sample_size)) for node in nodes]
    env.process(monitor(env, nodes))
    env.run(until=num_rounds)
    print('END')
    print(''.join('%i' % node.color.value for node in nodes))
