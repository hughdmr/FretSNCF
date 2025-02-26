# Fret_SNCF

# Contexte

DEB travaille sur les trains d'arrivee
FOR & DEP travaillent sur les trains de depart

# Variables de décision

m = machine [DEB,FOR,DEP]
t = train = [ta, td]
ta = train arrivee = [1,2,3...]: DEB
td = train de depart = [8,9,10,...] : FOR & DEP
h = temps (en minute pour 7 jours) = [range(0,1400*7)]
w = wagon, associé a 2 trains

m_t_h = 1 si la machine travaille sur le train t au temps h, 0 sinon.

# Contraintes

Pour ta en FOR, on doit avoir les wagons d'un td deja passe en DEB.

# Fonction objectif
