"""Tests du module de télémétrie.

Deux tests vous sont fournis en exemple : ils montrent le style attendu.
Tout le reste est à écrire — voir le TD 1.
"""

import pytest

from fleet_api.models import Position
from fleet_api.telemetry import battery_percentage, distance_m 
from fleet_api.telemetry import is_low_battery, path_length_m, average_speed_mps
from fleet_api.telemetry import estimate_runtime_minutes, median_voltage_mv
from fleet_api.telemetry import robot_state, detect_voltage_dropouts, fleet_summary
from fleet_api.telemetry import Reading, Position, RobotState

# fonction utilitaire pour créer une mesure de tension à partir d'une valeur en mV.'''
def mesure(tension, en_charge=False):
    return Reading(robot_id="r1", timestamp_s=0.0, voltage_mv=tension, position=Position(0, 0), is_charging=en_charge)
# ---------------------------------------------------------------------------
# Exemple 1 — un test simple, avec un cas nominal et les deux bornes.
# ---------------------------------------------------------------------------


def test_battery_percentage_bornes_et_cas_nominal():
    """La conversion est linéaire et bornée à [0, 100]."""
    assert battery_percentage(12_600) == 100.0
    assert battery_percentage(10_500) == 0.0
    assert battery_percentage(11_550) == 50.0
    # Hors bornes : on sature, on ne dépasse pas.
    assert battery_percentage(13_000) == 100.0
    assert battery_percentage(9_000) == 0.0


# ---------------------------------------------------------------------------
# Exemple 2 — le même test écrit en paramétré, quand les cas se ressemblent.
# On teste aussi que l'erreur attendue est bien levée.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "attendu"),
    [
        (Position(0, 0), Position(3, 4), 5.0),  # triplet pythagoricien
        (Position(0, 0), Position(0, 0), 0.0),  # distance à soi-même
        (Position(1, 1), Position(-2, -3), 5.0),  # coordonnées négatives
        (Position(3, 4), Position(0, 0), 5.0),  # symétrie
    ],
)
def test_distance_m(a, b, attendu):
    """La distance est euclidienne, positive et symétrique."""
    assert distance_m(a, b) == pytest.approx(attendu)


def test_battery_percentage_rejette_des_bornes_incoherentes():
    """Une plage de tension invalide lève une ValueError."""
    with pytest.raises(ValueError, match="strictement supérieur"):
        battery_percentage(11_000, empty_mv=12_000, full_mv=11_000)


# ---------------------------------------------------------------------------
# À vous. Huit fonctions de fleet_api.telemetry n'ont aucun test :
#
#   is_low_battery, path_length_m, average_speed_mps, estimate_runtime_minutes,
#   median_voltage_mv, robot_state, detect_voltage_dropouts, fleet_summary
#
# Écrivez-les en vous appuyant sur les docstrings, qui font foi.
# Trois de ces fonctions ne respectent pas leur spécification.
# ---------------------------------------------------------------------------

''' 
is_low_battery : Vérifie si le pourcentage de batterie est inférieur au seuil.
Cas attendus : 
- Pourcentage inférieur au seuil : retourne True
- Pourcentage égal au seuil : retourne False
- Pourcentage supérieur au seuil : retourne False
'''

def test_is_low_battery():
    """Test de la fonction is_low_battery."""
    assert is_low_battery(15.0) == True  # inférieur au seuil
    assert is_low_battery(20.0) is True  # égal au seuil : en alerte
    assert is_low_battery(25.0) == False  # supérieur au seuil
    


'''
path_length_m : Calcule la longueur totale d'un chemin défini par une liste de positions.
Cas attendus :
- Liste vide : retourne 0.0
- Liste avec une seule position : retourne 0.0
- Liste avec plusieurs positions : retourne la somme des distances entre positions consécutives 
'''
def test_path_length_m():
    """Test de la fonction path_length_m."""
    assert path_length_m([]) == 0.0  # liste vide
    assert path_length_m([Position(0, 0)]) == 0.0  # une seule position
    assert path_length_m([Position(0, 0), Position(3, 4)]) == pytest.approx(5.0)  # deux positions
    assert path_length_m([Position(0, 0), Position(3, 4), Position(6, 8)]) == pytest.approx(10.0)  # trois positions
    assert path_length_m([Position(0, 0), Position(1, 1), Position(2, 2)]) == pytest.approx(2.8284271247461903)  # diagonale
    assert path_length_m([Position(0, 0), Position(0, 0), Position(0, 0), Position(0, 0)]) == pytest.approx(0.0)  # 4 positions identiques


'''
average_speed_mps : Calcule la vitesse moyenne sur un trajet, en mètres par seconde.
Cas attendus :
- Longueur du trajet nulle ou négative : retourne None
- Durée du trajet nulle ou négative : retourne None
- Longueur et durée positives : retourne la vitesse moyenne
'''

def test_average_speed_mps():
    """Test de la fonction average_speed_mps."""
    assert average_speed_mps(10.0, 5.0) == 2.0  # vitesse moyenne
    assert average_speed_mps(10.0, 0.0) is None  # durée nulle
    assert average_speed_mps(0.0, 5.0) == 0.0  # longueur nulle
    assert average_speed_mps(10.0, -5.0) is None  # durée négative


'''
estimate_runtime_minutes : Estime l'autonomie restante en minutes.
Cas attendus :
- Consommation nulle ou négative : retourne None
- Consommation positive : retourne l'autonomie restante en minutes  
'''

def test_estimate_runtime_minutes():
    """Test de la fonction estimate_runtime_minutes."""
    assert estimate_runtime_minutes(50.0, 5.0) == pytest.approx(10.0)  # autonomie restante
    assert estimate_runtime_minutes(50.0, 0.0) is None  # consommation nulle
    assert estimate_runtime_minutes(50.0, -5.0) is None  # consommation négative
    assert estimate_runtime_minutes(100.0, 10.0) == pytest.approx(10.0)  # autonomie restante


'''
median_voltage_mv : Calcule la médiane des tensions mesurées.
Cas attendus :
- Liste vide : retourne None
- Liste avec un élément : retourne cet élément
- Liste avec un nombre pair d'éléments : retourne la moyenne des deux éléments du milieu
- Liste avec un nombre impair d'éléments : retourne l'élément du milieu
'''
def test_median_voltage_mv():
    """Test de la fonction median_voltage_mv."""
    assert median_voltage_mv([]) is None  # liste vide
    assert median_voltage_mv([mesure(12000)]) == 12000.0  # un élément
    assert median_voltage_mv([mesure(12000), mesure(13000)]) == 12500.0  # deux éléments
    assert median_voltage_mv([mesure(12000), mesure(13000), mesure(14000)]) == 13000.0  # trois éléments
    assert median_voltage_mv([mesure(12000), mesure(13000), mesure(14000), mesure(15000)]) == 13500.0  # quatre éléments


'''
robot_state : Détermine l'état du robot en fonction de la tension mesurée.
Cas attendus :
- Tension inférieure à 11000 mV : OFFLINE
- Tension entre 11000 mV et 11500 mV : LOW_BATTERY
- Tension entre 11500 mV et 12500 mV : OPERATION
- Tension supérieure à 12500 mV : CHARGING
- Temps supérieuxr à 120 secondes : OFFLINE
- Temps inférieur ou égal à 120 secondes : OPERATIONAL
'''
def test_robot_state():
    """Test de la fonction robot_state."""
    assert robot_state(mesure(12000), now_s=200.0) == RobotState.OFFLINE  # hors ligne
    assert robot_state(mesure(12000), now_s=120) == RobotState.OPERATIONAL # opérationnel
    assert robot_state(mesure(10000), now_s=60) == RobotState.LOW_BATTERY  # opérationnel  
    assert robot_state(mesure(12500, en_charge=True), now_s=10) == RobotState.CHARGING  # en charge
    #assert robot_state(mesure(11000), en_charge=False, now_s=10) == RobotState.LOW_BATTERY  # batterie faible et mention de la recharge


'''
detect_voltage_dropouts : Détecte les coupures de tension dans une liste de mesures.
Cas attendus :
- Liste vide : retourne une liste vide
- Liste avec une seule mesure : retourne une liste vide
- Liste avec plusieurs mesures : retourne une liste de tuples (timestamp, voltage) pour chaque coup
ure détectée
- La coupure est définie comme une mesure avec une tension inférieure à 11000 mV
'''

def test_detect_voltage_dropouts():
    """Test de la fonction detect_voltage_dropouts."""
    assert detect_voltage_dropouts([] , max_drop_mv=500 ) == []  # liste vide
    assert detect_voltage_dropouts([mesure(12600), mesure(12000)], max_drop_mv=500) == [1]  # une coupure détectée
    assert detect_voltage_dropouts([mesure(12000), mesure(11800)], max_drop_mv=500) == []  # petite baisse

'''
fleet_summary : Résume l'état d'une flotte de robots à partir d'une liste de mesures.
Cas attendus :
- Liste vide : retourne un dictionnaire avec des compteurs à zéro
- Liste avec des mesures : retourne le nombre, leur charge moyenne et le nombre de robots avec une 
batterie faible
'''
def test_fleet_summary():
    """Test de la fonction fleet_summary."""
    assert fleet_summary([]) == {'robot_count': 0, 'average_battery_pct': 0.0, 'low_battery_count': 0}  # flotte vide
    assert fleet_summary([mesure(12600), mesure(10500)], threshold_pct=20.0) == {'robot_count': 2, 'average_battery_pct': 50.0, 'low_battery_count': 1} 
    assert fleet_summary([mesure(12600), mesure(12000), mesure(11000)], threshold_pct=20.0) == {'robot_count': 3, 'average_battery_pct': 65.1, 'low_battery_count': 0}  # 100 %, 71,4 %, 23,8 % : aucun sous 20 %
    assert fleet_summary([mesure(12600), mesure(12000), mesure(11000), mesure(10500)], threshold_pct=20.0) == {'robot_count': 4, 'average_battery_pct': 48.8, 'low_battery_count': 1}  # 100 %, 71,4 %, 23,8 %, 0 % : seul le 0 % en alerte   