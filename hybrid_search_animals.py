# -*- coding: utf-8 -*-


import itertools
import os
import random

from psychopy import core, visual, gui, data, event

# the first window after running the experiment with empty fields for name and age of the participant
dlg = gui.Dlg(title=u"Информация")
dlg.addText(u'Об испытуемом:')
dlg.addField(u'Фамилия:')
dlg.addField(u'Возраст:')
# choose how many animals participant will memorize
dlg.addField(u'Количество запоминаемых объектов:', choices=[2, 4, 8, 16])
ok_data = dlg.show()  # show dialog and wait for OK or Cancel
if dlg.OK:
    choice_mem_set = int(ok_data[2])  # number of memorizing objects from GUI
else:
    print('user cancelled')
    exit()

# creating window for all experiment
window = visual.Window([1920, 1080], monitor="test_monitor", units="pix",
                       color=(250, 250, 250))

# picture's directory
pics_dir = 'pictures'

# instruction to the experiment
message = visual.TextStim(window, color=(0, 0, 0),
                          text=u'В данном эксперименте Вам предстоит '
                               u'запоминать категории объектов, ')
message.draw()
window.flip()

event.waitKeys(keyList=["space"])

event.clearEvents()

clock = core.Clock()

# making sets of pictures' names
animals = set(range(0, 32))
non_tar_cat = set(range(32, 62))
# set of target stimuli which are animals
# creating target stimuli according to chosen number in GUI
target_animals = set(random.sample(animals, choice_mem_set))


def get_shift(set_size):
    cell = 230

    def shift(x, y):
        return (x * cell / 2), (y * cell / 2)

    if set_size == 2:
        return shift(2, 1)
    if set_size == 4:
        return shift(2, 2)
    if set_size == 8:
        return shift(4, 2)
    if set_size == 16:
        return shift(4, 4)


# making positions of target stimuli
def get_possible_target_positions():
    x_shift, y_shift = get_shift(choice_mem_set)

    def create_target_pos(x, y, cell=230, margin=90):
        return (x * cell + margin - x_shift,
                y * cell + margin - y_shift)

    def get_all_pos(xn, yn):
        tr_positions = set()
        for y in range(0, yn):
            for x in range(0, xn):
                tr_positions.add(create_target_pos(x, y))
        return tr_positions

    ts_size = len(target_animals)
    if ts_size == 2:
        return get_all_pos(2, 1)
    if ts_size == 4:
        return get_all_pos(2, 2)
    if ts_size == 8:
        return get_all_pos(4, 2)
    if ts_size == 16:
        return get_all_pos(4, 4)


# function which shows targets on screen
def show_stimuli(name, pos):
    stim = visual.ImageStim(window, pos=pos)
    stim.setImage(os.path.join(pics_dir, name))
    stim.size = [140, 140]
    stim.draw()


# creating readable names of targets
target_names = map(lambda x: str(x) + '.jpg', target_animals)
# using functions to show target stimuli and making "space" key button as a flip to the experiment
target_positions = get_possible_target_positions()
target_stimuli = zip(target_names, target_positions)
for (n, pos) in target_stimuli:
    show_stimuli(n, pos)
window.flip()


# there is 8 permutations of showing destructors during the experiment
# first column contains number of animal destructors which will appear on the screen
# second column contains number of non-target category destructors
variants = [
    (4, 0),
    (0, 4),
    (4, 4),
    (8, 0),
    (0, 8),
    (8, 4),
    (4, 8),
    (8, 8),
]
# multiplying all variants of permutation on 64, cause each permutation contains 64 trails
all_trials = 512
permutations = variants * (all_trials / len(variants))
random.shuffle(permutations)


# it is 50 % chance of presence target stimuli during the experiment
# function creates [1, 0, 1, ...] whereas 1 == presence, 0 == absence
def create_presence():
    pres = list(itertools.repeat(0, all_trials / 2)) + list(itertools.repeat(1, all_trials / 2))
    random.shuffle(pres)
    return pres


presence = create_presence()


# making presence for each permutation
def create_iterations():
    for i in range(0, len(permutations)):
        a, b = permutations[i]
        permutation_presence = presence[i]  # 64 [1, 0...] for this permutation
        yield (a, b, permutation_presence)


iterations = list(create_iterations())


# main function to create a list with pictures for one trail
# [pics_on_screen] contains numbers-names of pictures
def get_trail_pics(a, b, p):
    pics_on_screen = []
    target_stim_wo_ts = animals - target_animals
    all_possible_dest = target_stim_wo_ts.union(non_tar_cat)
    if a == 0 or b == 0:  # we take into account the condition under which one of the values in permutation may be zero
        destr_animals = set(random.sample(target_stim_wo_ts, a))
        destr_non_target = set(random.sample(non_tar_cat, b))
        all_destr = destr_animals.union(destr_non_target)
    else:
        all_destr = set(random.sample(all_possible_dest, a + b))
    if p:
        # choosing randomly target stimulus and add to the [pics_on_screen]
        ts = random.choice(list(target_animals))
        pics_on_screen.append(ts)
        # choosing randomly destructors depending on the permutation with added space for target
        destructors_animals = set(random.sample(all_destr, a + b - 1))
        pics_on_screen += destructors_animals
    else:
        # choosing randomly destructors depending on the permutation without target
        destructors_animals = set(random.sample(all_destr, a + b))
        pics_on_screen += destructors_animals
    return pics_on_screen


# this function creates positions of objects for all objects in trail
def get_possible_trail_positions():
    def create_pos(x, y, cell=184, margin=22):
        return (x * cell + margin + random.randint(-10, 10) - 368,
                y * cell + margin + random.randint(-10, 10) - 368)

    positions = set()
    for x in range(0, 5):
        for y in range(0, 5):
            positions.add(create_pos(x, y))
    return positions

# we need to create [stim_list] for trail handler to to record the results of participant's the selection
stim_list = []
for (a, b, p) in iterations:
    stim_list.append({"set_size": str(a) + "+" + str(b), "presence": p})

trials = data.TrialHandler(stim_list, 1, method="sequential",
                           dataTypes=["time", "choice"],
                           extraInfo={"name": ok_data[0], "age": ok_data[1],
                                      "mem_set": ok_data[2]})

event.waitKeys(keyList=["space"])
window.flip()

# fill the experiment
# each loop equals to one trail
for trial in trials:
    p = trial["presence"]
    set_size = trial["set_size"]
    a, b = str(set_size).split("+")
    pics_on_screen = get_trail_pics(int(a), int(b), p)
    names = map(lambda x: str(x) + '.jpg', pics_on_screen)
    possible_positions = get_possible_trail_positions()
    positions = random.sample(possible_positions, len(pics_on_screen))
    stimuli = zip(names, positions)
    for (n, pos) in stimuli:
        show_stimuli(n, pos)
    window.flip()
    clock.reset()

    key = event.waitKeys(keyList=["left", "right", "escape"])
    time = clock.getTime()
    trials.data.add("time", time)
    if key:
        trials.data.add("choice", key[0])
        if key[0] == "escape":
            break
    else:
        trials.data.add("choice", "no choice")
    window.flip()
    event.clearEvents()
# create an excel file with all information about participant + each trail
excel = trials.saveAsExcel(fileName='exp ' + ok_data[0],
                           sheetName='rawData ' + str(choice_mem_set),
                           stimOut=['set_size', 'presence'],
                           dataOut=['time_raw', 'choice_raw'])


message = visual.TextStim(window, text=u'Спасибо, что были с нами!')
message.draw()
window.flip()
core.wait(5)
