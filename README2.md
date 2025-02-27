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
w = wagon = [w1, w2, w3], associé a 2 trains

m_t_h = 1 si la machine travaille sur le train t au temps h, 0 sinon.

# Contraintes

Pour td en FOR, on doit avoir les wagons d'un ta deja passe en DEB.

for train*depart in td:
for w in wagons[train_depart]
train_arrivee = wagon_to_train_arrivee(w) # Le dernier instant où FOR a travaillé doit être 60 min avant le premier instant où DEG travaille
model.addConstr(
max*([h _ m*t_h["DEB", t_a, h] for h in H]) <= min*([h _ m*t_h["FOR", t_d, h] for h in H]),
name=f"Deb_before_For*{t*a}*{t_d}"
)

# Fonction objectif
