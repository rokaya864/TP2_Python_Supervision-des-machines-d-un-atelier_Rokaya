"""Supervision d'un atelier : référentiel des machines, relevés capteurs, alertes et rapport."""
import csv
import json
import math
import re
from datetime import datetime
from pathlib import Path

from exceptions import FichierInvalide, ReleveInvalide

COLONNES = ("machine", "horodatage", "temperature", "vibration")

# Un relevé valide est un tuple : (machine, horodatage, temperature, vibration)
Releve = tuple[str, datetime, float, float]


# --- Étape 1 : le référentiel des machines (JSON, dictionnaires, ensembles) --------------------
import json
from pathlib import Path
from exceptions import FichierInvalide

def charger_machines(chemin: Path) -> dict:
    """
    Lit le fichier JSON des machines et renvoie un dictionnaire {id: fiche}.
    Lève FichierInvalide si un identifiant est présent plusieurs fois.
    """
    # 1. Ouverture du fichier JSON en UTF-8
    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)
    
    machines = {}
    
    # 2. Parcours de la liste et construction du dictionnaire
    for fiche in donnees:
        m_id = fiche["id"]
        # Vérification des doublons
        if m_id in machines:
            raise FichierInvalide(f"identifiant en double: {m_id}")
        machines[m_id] = fiche
        
    return machines


def ateliers(machines: dict) -> set:
    """
    Renvoie l'ensemble (set) des ateliers uniques sans doublons.
    """
    # Comprehension d'ensemble en une seule ligne
    return {m["atelier"] for m in machines.values()}
# --- Étape 3 : valider une ligne (exceptions, tuples) -------------------------------------------
import math
from datetime import datetime
from exceptions import ReleveInvalide


def lire_nombre(texte: str, champ: str, numero: int) -> float:
    """Valide et convertit une chaîne en float.
    
    Gère les virgules décimales, les champs vides, les valeurs non numériques et nan/inf.
    """
    texte_nettoye = texte.strip().replace(",", ".")
    
    if not texte_nettoye:
        raise ReleveInvalide("valeur manquante", numero, champ)
        
    try:
        valeur = float(texte_nettoye)
    except ValueError:
        # Ajout de l'espace avant les deux-points
        raise ReleveInvalide(f"valeur non numérique : {texte.strip()!r}", numero, champ)
        
    if math.isnan(valeur) or math.isinf(valeur):
        # Ajout de l'espace avant les deux-points
        raise ReleveInvalide(f"valeur non finie : {texte.strip()!r}", numero, champ)
        
    return valeur


def parser_releve(brut: dict, numero: int, machines: dict) -> tuple:
    """Valide et convertit un dictionnaire de ligne CSV en tuple (machine, horodatage, temp, vib)."""
    # 1. Validation de la machine
    m_raw = brut.get("machine", "").strip()
    m_upper = m_raw.upper()
    if m_upper not in machines:
        # Ajout de l'espace avant les deux-points
        raise ReleveInvalide(f"machine inconnue : {m_raw!r}", numero, "machine")
        
    # 2. Validation de l'horodatage
    h_raw = brut.get("horodatage", "").strip()
    try:
        dt = datetime.fromisoformat(h_raw)
    except ValueError:
        # Ajout de l'espace avant les deux-points
        raise ReleveInvalide(f"horodatage invalide : {h_raw!r}", numero, "horodatage") from None
        
    # 3. Validation de la température et de la vibration
    temp = lire_nombre(brut.get("temperature", ""), "temperature", numero)
    vib = lire_nombre(brut.get("vibration", ""), "vibration", numero)
    
    # 4. Vérification vibration non négative
    if vib < 0:
        val_str = brut.get("vibration", "").strip()
        # Ajout de l'espace avant les deux-points
        raise ReleveInvalide(f"vibration négative : {val_str}", numero, "vibration")
        
    return (m_upper, dt, temp, vib)

# --- Étape 4 : lire le fichier (CSV, générateur, collecte des erreurs) ---------------------------
import csv
from pathlib import Path
from exceptions import FichierInvalide, ReleveInvalide

# Colonnes obligatoires attendues dans le CSV
COLONNES = ["machine", "horodatage", "temperature", "vibration"]


def lignes_csv(chemin: Path):
    """Générateur qui lit le CSV et produit (numero_ligne, brut_dict)."""
    with open(chemin, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        
        # Vérification des colonnes attendues et identification des colonnes manquantes
        if reader.fieldnames is None:
            raise FichierInvalide("fichier CSV vide ou invalide")
            
        manquantes = [col for col in COLONNES if col not in reader.fieldnames]
        if manquantes:
            raise FichierInvalide(f"colonnes manquantes: {', '.join(manquantes)}")
            
        for i, ligne in enumerate(reader, start=2):
            yield (i, ligne)


def lire_releves(chemin: Path, machines: dict) -> tuple[list, list]:
    """Lit les relevés CSV et les sépare en relevés valides et erreurs."""
    releves = []
    erreurs = []
    
    for numero, brut in lignes_csv(chemin):
        try:
            releve = parser_releve(brut, numero, machines)
            releves.append(releve)
        except ReleveInvalide as err:
            erreurs.append(err)
            
    return (releves, erreurs)


def ecrire_rejets(erreurs: list, chemin: Path) -> None:
    """Écrit le fichier CSV rejets.csv contenant les erreurs détectées."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    
    with open(chemin, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["ligne", "champ", "message"])
        
        for err in erreurs:
            writer.writerow([err.ligne, err.champ, err.message])
# --- Étape 5 : analyser (dictionnaires, compréhensions) ------------------------------------------
# --- Étape 5 : analyser (dictionnaires, compréhensions) ------------------------------------------
def par_machine(releves: list[Releve]) -> dict[str, list[Releve]]:
    """Regroupe les relevés par machine : {machine: [relevés dans l'ordre du fichier]}."""
    resultat = {}
    for r in releves:
        machine = r[0]
        resultat.setdefault(machine, []).append(r)
    return resultat


def moyennes(releves: list[Releve]) -> dict[str, tuple[float, float]]:
    """{machine: (température moyenne arrondie à 0,1 ; vibration moyenne arrondie à 0,01)}."""
    groupes = par_machine(releves)
    resultat = {}
    for machine, liste in groupes.items():
        somme_temp = sum(r[2] for r in liste)
        somme_vib = sum(r[3] for r in liste)
        nb = len(liste)
        temp_moy = round(somme_temp / nb, 1)
        vib_moy = round(somme_vib / nb, 2)
        resultat[machine] = (temp_moy, vib_moy)
    return resultat


def alertes(releves: list[Releve], machines: dict[str, dict]) -> list[tuple[str, datetime, str]]:
    """Liste des dépassements de seuil (machine, horodatage, motif), triée par horodatage puis machine."""
    liste_alertes = []
    
    for machine, horodatage, temperature, vibration in releves:
        fiche = machines.get(machine)
        if not fiche:
            continue
        
        temp_max = fiche["temp_max"]
        vib_max = fiche["vib_max"]
        
        # Le seuil est strict : une valeur égale au seuil n'est pas une alerte
        if temperature > temp_max:
            motif = f"température {temperature} > {temp_max}"
            liste_alertes.append((machine, horodatage, motif))
            
        if vibration > vib_max:
            motif = f"vibration {vibration} > {vib_max}"
            liste_alertes.append((machine, horodatage, motif))
            
    # Tri par horodatage, puis par machine
    liste_alertes.sort(key=lambda x: (x[1], x[0]))
    return liste_alertes


def machines_silencieuses(releves: list[Releve], machines: dict[str, dict]) -> set[str]:
    """Les machines du référentiel qui n'ont envoyé aucun relevé valide (capteur en panne ?)."""
    machines_avec_releves = {r[0] for r in releves}
    return set(machines.keys()) - machines_avec_releves
# --- Étape 6 : trier ---------------------------------------------------------------------------
# --- Étape 6 : trier ---------------------------------------------------------------------------
def classement(releves: list[Releve], machines: dict[str, dict]) -> list[tuple[str, int]]:
    """[(machine, nombre d'alertes)] pour TOUTES les machines, la plus alertée d'abord, puis par identifiant."""
    compteurs = {m: 0 for m in machines}
    liste_alt = alertes(releves, machines)
    
    for machine, _, _ in liste_alt:
        if machine in compteurs:
            compteurs[machine] += 1
            
    return sorted(compteurs.items(), key=lambda item: (-item[1], item[0]))


def top_vibrations(releves: list[Releve], n: int = 3) -> list[Releve]:
    """Les n relevés de plus forte vibration, du plus fort au plus faible."""
    return sorted(releves, key=lambda r: r[3], reverse=True)[:n]


# --- Étape 7 : le rapport JSON ------------------------------------------------------------------
def construire_rapport(releves: list[Releve], erreurs: list[ReleveInvalide], machines: dict[str, dict]) -> dict:
    """Le rapport sous forme d'un dictionnaire prêt pour json.dump (pas de datetime, pas d'ensemble)."""
    moy = moyennes(releves)
    
    # Formatage des moyennes pour le rapport (machine: {"temperature": ..., "vibration": ...})
    moyennes_formatees = {
        m: {"temperature": t, "vibration": v} 
        for m, (t, v) in sorted(moy.items())
    }
    
    # Formatage des alertes (heure au format "09:00")
    liste_alt = alertes(releves, machines)
    alertes_formatees = [
        {
            "machine": m,
            "heure": h.strftime("%H:%M"),
            "motif": motif
        }
        for m, h, motif in liste_alt
    ]
    
    # Classement : identifiants des machines ayant au moins une alerte, dans l'ordre du classement
    classement_brut = classement(releves, machines)
    machines_a_surveiller = [m for m, nb in classement_brut if nb > 0]
    
    return {
        "releves_valides": len(releves),
        "lignes_rejetees": len(erreurs),
        "moyennes": moyennes_formatees,
        "alertes": alertes_formatees,
        "classement": machines_a_surveiller,
        "machines_silencieuses": sorted(list(machines_silencieuses(releves, machines)))
    }


def ecrire_rapport(rapport: dict, chemin: Path) -> None:
    """Écrit le rapport en JSON indenté, accents conservés."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

# --- Étape 8 (à la maison) : le journal des événements (expressions régulières) ------------------
# --- Étape 8 : Journal des événements (expressions régulières) -----------------------------------
MOTIF_EVENEMENT = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<heure>\d{2}:\d{2}:\d{2})\s+"
    r"\[(?P<machine>M-\d{2})\]\s+"
    r"(?P<type>[A-Z]+)\s+"
    r"code=(?P<code>[A-Z]\d{2})"
    r"(?:\s+duree=(?P<duree>\d+))?"
)


def lire_evenements(chemin: Path):
    """Générateur : lit le journal ligne par ligne et produit un dictionnaire par événement valide."""
    with open(chemin, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne_propre = ligne.strip()
            match = MOTIF_EVENEMENT.fullmatch(ligne_propre)
            if match:
                donnees = match.groupdict()
                # Conversion de la durée en int si elle est présente, sinon None
                duree_str = donnees.get("duree")
                duree = int(duree_str) if duree_str is not None else None
                
                yield {
                    "machine": donnees["machine"],
                    "type": donnees["type"],
                    "code": donnees["code"],
                    "heure": donnees["heure"],
                    "duree": duree
                }


def temps_arret(evenements) -> dict[str, int]:
    """Calcule la durée totale des événements ARRET par machine, en minutes."""
    totaux = {}
    for ev in evenements:
        if ev["type"] == "ARRET" and ev["duree"] is not None:
            machine = ev["machine"]
            duree = ev["duree"]
            totaux[machine] = totaux.get(machine, 0) + duree
    return totaux
