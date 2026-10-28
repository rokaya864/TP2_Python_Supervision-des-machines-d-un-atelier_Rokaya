class AtelierError(Exception):
    """Classe de base pour toutes les exceptions du projet."""
    pass


class FichierInvalide(AtelierError):
    """Signale un fichier entier inutilisable."""
    pass


class ReleveInvalide(AtelierError):
    """Signale une erreur sur une ligne spécifique d'un fichier de relevés."""

    def __init__(self, message: str, ligne: int, champ: str):
        """Initialise l'exception avec les détails de la ligne invalide."""
        self.message = message
        self.ligne = ligne
        self.champ = champ
        
        # Format exact exigé par test_etape2.py
        super().__init__(f"ligne {ligne}, champ '{champ}' : {message}")