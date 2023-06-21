# PyLure

This is a simple toolkit I created to explore the data files used by 
1992 point'n'click game 
[Lure of the Temptress](https://en.wikipedia.org/wiki/Lure_of_the_Temptress).

Back in the day I was a big fan of 
[Beneath A Steel Sky](https://en.wikipedia.org/wiki/Beneath_a_Steel_Sky), which
was produced 2 years later by the same team, but I didn't play lure until a
few weeks ago while trying to get over a chest infection. It's an OK game,
but the path-finding in the SCUMMVM implementation seems a bit off, and I 
wanted to see if I could do something about it. 

Currently, this just spits out some details about the rooms that are used in the
game. This info is extracted from the `lure.dat` file which is originally taken from the
SCUMMVM repo [here](https://github.com/scummvm/scummvm/tree/master/dists/engine-data)
