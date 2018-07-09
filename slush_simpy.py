#!/usr/bin/env python3

import enum
import itertools
import random

import curtsies
import simpy


#  C  set of correct nodes      c  number of correct nodes
#  B  set of byzantine node     b  number of byzantine nodes
#  N  set of all nodes          n  number of nodes

num_rounds = 100    # m in the whitepaper
num_nodes = 100     # n in the whitepaper
sample_size = 5     # k in the whitepaper
sample_threshold = 0.6     # α in the whitepaper


assert sample_size < num_nodes
assert 0.5 < sample_threshold < 1.0


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return itertools.zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)


class Color(enum.Enum):
    UNCOLORED = 0
    RED = 1
    BLUE = 2


class SlushNode:
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
            # TODO Does node n always get scheduled before n+1?
            # TODO Does that affect the outcome? How?
            contacts = random.sample(set(nodes).difference({self}), sample_size)
            replies = [contact.on_query(self.color) for contact in contacts]

            for color in [Color.RED, Color.BLUE]:
                if replies.count(color) > sample_threshold * sample_size:
                    self.color = color
            yield self.env.timeout(1)


def node_portrayal(node):
    bg = ['black', 'red', 'blue'][node.color.value]
    return curtsies.fmtstr(' ', bg=bg)


def monitor(env, nodes):
    # TODO Does this run at the end of a step? beginning? indeterminate?
    with curtsies.CursorAwareWindow() as win:
        while True:
            lines = grouper(win.width, nodes)
            vis = curtsies.fsarray([
                curtsies.fmtstr('').join(
                    node_portrayal(node) for node in line if node)
                for line in lines
            ])
            win.render_to_terminal(vis)
            yield env.timeout(delay=1)


if __name__ == '__main__':
    env = simpy.rt.RealtimeEnvironment()
    initial_colors = [Color(random.randint(0, 2)) for i in range(num_nodes)]
    nodes = [SlushNode(env, color) for color in initial_colors]
    #print('BEGIN')
    #print(''.join('%i' % node.color.value for node in nodes))
    procs = [env.process(node.run(nodes, sample_size)) for node in nodes]
    env.process(monitor(env, nodes))
    env.run(until=num_rounds)
    #print('END')
    #print(''.join('%i' % node.color.value for node in nodes))
