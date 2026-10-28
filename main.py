"""Programme principal : lit les relevés du jour, écrit les rejets et le rapport, affiche un résumé."""
from pathlib import Path

from atelier import (charger_machines, construire_rapport, ecrire_rapport, ecrire_rejets, lire_releves)
from exceptions import AtelierError

ICI = Path(__file__).parent
DONNEES = ICI / "donnees"
SORTIES = ICI / "sorties"


def main() -> int:
    """Renvoie 0 si tout s'est bien passé, 1 si un fichier est inutilisable."""
    try:
        machines = charger_machines(DONNEES / "machines.json")
        releves, erreurs = lire_releves(DONNEES / "releves.csv", machines)
    except (AtelierError, FileNotFoundError) as e:
        print(f"Erreur : {e}")
        return 1

    SORTIES.mkdir(exist_ok=True)
    
    # Écriture des rejets et du rapport
    ecrire_rejets(erreurs, SORTIES / "rejets.csv")
    
    rapport_dict = construire_rapport(releves, erreurs, machines)
    ecrire_rapport(rapport_dict, SORTIES / "rapport.json")
    
    # Affichage du résumé demandé
    nb_valides = len(releves)
    nb_rejetes = len(erreurs)
    nb_alertes = len(rapport_dict["alertes"])
    machines_surveiller = ", ".join(rapport_dict["classement"])
    silencieuses = ", ".join(rapport_dict["machines_silencieuses"])
    
    print(f"{nb_valides} relevés valides, {nb_rejetes} lignes rejetées")
    print(f"{nb_alertes} alertes; machines à surveiller {machines_surveiller}")
    print(f"Sans relevé : {silencieuses}")
    print("Fichiers écrits dans sorties/ rejets.csv, rapport.json")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())