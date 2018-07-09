#!/usr/bin/env python3

import enum
import itertools
import random

import curtsies
import simpy


#  C  set of correct nodes      c  number of correct nodes
#  B  set of byzantine node     b  number of byzantine nodes
#  N  set of all nodes          n  number of nodes

num_rounds = 20    # m in the whitepaper
num_nodes = 2000     # n in the whitepaper
sample_size = 5     # k in the whitepaper
sample_threshold = 0.6     # α in the whitepaper


assert sample_size < num_nodes
assert 0.5 < sample_threshold < 1.0


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(itertools.islice(it, size)), ())


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


def display_color(node):
    return ['black', 'red', 'blue'][node.color.value]


def monitor(env, nodes):
    # TODO Does this run at the end of a step? beginning? indeterminate?
    assert len(nodes) % 2 == 0, "Odd number of nodes won't render correctly"
    with curtsies.CursorAwareWindow() as win:
        while True:
            chunks = list(chunk(nodes, win.width*2))
            vis = curtsies.FSArray(len(chunks), win.width*2)
            for i, row in enumerate(chunks):
                for j in range(0, len(row), 2):
                    fg = display_color(row[j])
                    bg = display_color(row[j+1])
                    vis[i, j//2] = curtsies.fmtstr('▀', fg=fg, bg=bg)
            win.render_to_terminal(vis)
            yield env.timeout(delay=1)


if __name__ == '__main__':
    env = simpy.rt.RealtimeEnvironment()
    initial_colors = [Color(random.randint(0, 2)) for i in range(num_nodes)]
    nodes = [SlushNode(env, color) for color in initial_colors]
    procs = [env.process(node.run(nodes, sample_size)) for node in nodes]
    env.process(monitor(env, nodes))
    env.run(until=num_rounds)
