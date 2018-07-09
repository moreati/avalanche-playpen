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

    def run(self, other_nodes, sample_size):
        while True:
            if self.color == Color.UNCOLORED:
                yield self.env.timeout(1)
                continue
            # TODO Does node n always get scheduled before n+1?
            # TODO Does that affect the outcome? How?
            contacts = random.sample(other_nodes, sample_size)
            replies = [contact.on_query(self.color) for contact in contacts]

            for color in [Color.RED, Color.BLUE]:
                if replies.count(color) > sample_threshold * sample_size:
                    self.color = color
                    break
            yield self.env.timeout(1)


def display_color(color_value):
    return ['black', 'red', 'blue'][color_value]


def monitor(env, nodes):
    # TODO Does this run at the end of a step? beginning? indeterminate?
    assert len(nodes) % 2 == 0, "Odd number of nodes won't render correctly"
    sep = curtsies.fmtstr('')
    cells = {
        (0, 0): curtsies.fmtstr('▀', fg=display_color(0), bg=display_color(0)),
        (0, 1): curtsies.fmtstr('▀', fg=display_color(0), bg=display_color(1)),
        (0, 2): curtsies.fmtstr('▀', fg=display_color(0), bg=display_color(2)),
        (1, 0): curtsies.fmtstr('▀', fg=display_color(1), bg=display_color(0)),
        (1, 1): curtsies.fmtstr('▀', fg=display_color(1), bg=display_color(1)),
        (1, 2): curtsies.fmtstr('▀', fg=display_color(1), bg=display_color(2)),
        (2, 0): curtsies.fmtstr('▀', fg=display_color(2), bg=display_color(0)),
        (2, 1): curtsies.fmtstr('▀', fg=display_color(2), bg=display_color(1)),
        (2, 2): curtsies.fmtstr('▀', fg=display_color(2), bg=display_color(2)),
    }
    with curtsies.CursorAwareWindow() as win:
        chunks = list(chunk(nodes, win.width*2))
        vis = curtsies.FSArray(len(chunks), win.width)
        while True:
            for i, row in enumerate(chunks):
                line = [
                    cells[row[j].color.value, row[j+1].color.value]
                    for j in range(0, len(row), 2)
                ]
                line = sep.join(line)
                vis[i] = line
            win.render_to_terminal(vis)
            yield env.timeout(delay=1)


if __name__ == '__main__':
    env = simpy.rt.RealtimeEnvironment()
    initial_colors = [Color(random.randint(0, 2)) for i in range(num_nodes)]
    nodes = [SlushNode(env, color) for color in initial_colors]
    procs = [env.process(node.run(tuple(set(nodes).difference({node})), sample_size)) for node in nodes]
    env.process(monitor(env, nodes))
    env.run(until=num_rounds)
