from pathlib import Path
from atelier import lire_evenements, temps_arret

def test_journal_evenements():
    chemin = Path("donnees/evenements.log")
    evenements = list(lire_evenements(chemin))
    
    assert len(evenements) == 8
    assert evenements[1] == {
        'machine': 'M-03', 
        'type': 'ARRET', 
        'code': 'E42', 
        'heure': '08:15:02', 
        'duree': 12
    }
    
    totaux = temps_arret(evenements)
    assert totaux == {'M-03': 20, 'M-02': 25, 'M-01': 40}