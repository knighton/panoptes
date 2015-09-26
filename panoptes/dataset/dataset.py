class Episode(object):
    """
    A single run of some input/output pairs against an Agent before resetting
    its state.
    """

    def __init__(self, pairs):
        self.pairs = pairs

    def show(self):
        for in_s, out in self.pairs:
            print '    %s' % in_s.encode('utf-8')
            if out:
                print '        > %s' % out.encode('utf-8')

    def evaluate(self, agent, uid):
        """
        Agent -> (num correct tests, num tests)
        """
        correct = 0
        total = 0
        for in_s, out in self.pairs:
            got_out = agent.put(uid, in_s)
            if out is not None:
                correct += out == got_out
                total += 1
        return correct, total


class Task(object):
    """
    A collection of Episodes that evaluate the performance of an Agent on the
    same kind of problem.
    """

    def __init__(self, name, episodes):
        self.name = name
        self.episodes = episodes

    def overview(self):
        num_ins = 0
        num_outs = 0
        for e in self.episodes:
            ins, outs = zip(*e.pairs)
            num_ins += len(ins)
            num_outs += len(filter(bool, outs))
        return self.name, len(self.episodes), num_ins, num_outs

    def preview(self, task_index, num_episodes_to_show):
        print
        print '  %d. %s:' % (task_index, self.name.encode('utf-8'))
        print
        for e in self.episodes[:num_episodes_to_show]:
            print
            e.show()

    def evaluate(self, agent):
        """
        Agent -> accuracy
        """
        correct = 0
        total = 0
        for episode in self.episodes:
            agent.reset()
            uid = agent.new_user()
            a, b = episode.evaluate(agent, uid)
            correct += a
            total += b
        return float(correct) / total


class Dataset(object):
    """
    A runner that sees how an Agent performs on different Tasks.
    """

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

    def overview(self):
        sss = [('#', 'task', 'episodes', 'inputs', 'questions')]
        for i, task in enumerate(self.tasks):
            ss = map(str, [i + 1] + list(task.overview()))
            sss.append(ss)
        zz = map(lambda aa: max(map(len, aa)), zip(*sss))
        for ss in sss:
            for i, s in enumerate(ss):
                z = zz[i]
                if i == 1:
                    s = s.ljust(z)
                else:
                    s = s.rjust(z)
                print s,
            print

    def preview(self, num_episodes_to_show=1):
        print 'Preview of %s:' % self.name.encode('utf-8')
        for i, task in enumerate(self.tasks):
            task.preview(i + 1, num_episodes_to_show)

    def evaluate(self, agent, out=None):
        names_accs = []
        for task in self.tasks:
            acc = task.evaluate(agent)
            names_accs.append((task.name, acc))

        if out:
            z = max(map(len, zip(*names_accs)[0]))
            for task, acc in names_accs:
                line = '%s %.3f\n' % (task.ljust(z), acc * 100)
                out.write(line)

        return float(sum(map(lambda (n, a): a, names_accs))) / len(names_accs)