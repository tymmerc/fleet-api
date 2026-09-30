# fleet-api

Mini-service de supervision d'une flotte de robots d'entrepôt.

Ce dépôt est le **fil rouge** du module *Usine Logicielle et CI/CD* (ESIA A3). Vous
allez le faire grossir séance après séance jusqu'à disposer d'une chaîne
d'intégration et de déploiement complète.

---

## Ce que fait le service

Les robots d'un entrepôt émettent régulièrement leur télémétrie : tension
batterie, position, état de charge. `fleet-api` la reçoit et en calcule des
indicateurs — niveau de charge, autonomie restante, distance parcourue, alertes
batterie, agrégats de flotte.

Le cœur métier vit dans `src/fleet_api/telemetry.py` : une dizaine de
**fonctions pures**, sans état ni entrée-sortie, donc directement testables.

## Démarrage

Prérequis : [uv](https://docs.astral.sh/uv/). Inutile d'installer Python vous-même :
uv télécharge la version voulue (≥ 3.12) au premier `uv sync`.

```bash
uv sync                 # installe les dépendances
uv run pytest -v        # lance la suite de tests
```

Vous devez obtenir **6 tests au vert**. Si ce n'est pas le cas, signalez-le
avant d'aller plus loin.

## Structure

```
src/fleet_api/
├── models.py       Position, Reading, RobotState
├── telemetry.py    les fonctions de calcul  ← l'objet du TD 1
├── store.py        stockage en mémoire ou PostgreSQL  (séance 5)
└── api.py          les endpoints HTTP                 (séance 5)
tests/
└── test_telemetry.py   3 tests d'exemple, le reste est à écrire
```

## Règles du jeu

1. **Les docstrings font foi.** Elles sont la spécification. Quand le code et la
   docstring divergent, c'est le code qui a tort. Ne modifiez jamais une
   docstring pour la faire coller à l'implémentation.
2. **On travaille par pull request.** À partir de la séance 2, `main` est
   protégée : plus de push direct.
3. **Un commit, une intention.** Le message dit *pourquoi*, pas *quoi* — le diff
   dit déjà quoi.

## Backlog

Évolutions possibles pour le rendu final, par ordre de difficulté croissante.
Vous n'avez pas à toutes les traiter : mieux vaut deux fonctionnalités bien
testées et bien intégrées que six bâclées.

- [ ] `GET /robots/{id}/history` — historique de télémétrie d'un robot
- [ ] Alerte sur immobilité prolongée (aucun déplacement depuis N minutes)
- [ ] `GET /fleet/heatmap` — densité de présence par zone de l'entrepôt
- [ ] Estimation du temps de charge restant
- [ ] Détection de dérive de calibration entre robots d'un même modèle
- [ ] Export Prometheus des indicateurs de flotte

## Progression du module

| Séance | Ce que vous ajoutez |
|---|---|
| 1 | Les tests manquants, un premier workflow |
| 2 | Pipeline lint / test / build, protection de `main` |
| 3 | Workflow réutilisable, pre-commit, Dependabot |
| 4 | Dockerfile multi-stage, docker compose |
| 5 | Build et publication d'image sur GHCR, scan de vulnérabilités |
| 6 | Couverture, typage, analyse statique, quality gate |
| 7 | Release versionnée, environnements, bascule et retour arrière |
| 8 | Revue croisée, finalisation |

## Mesures du pipeline (TD 2)

Durées relevées dans l'onglet Actions (durée totale du run, de son déclenchement à la fin de la dernière tâche).

| Version du pipeline | Durée totale | Détail des tâches |
|---|---|---|
| TD 1 : une seule tâche (tests) | 15 s | tests 15 s |
| Étape 1 : lint, test et build en parallèle | 15 s | build 7 s · lint 11 s · test 12 s |
| Étape 2a : cache froid (cache supprimé avant le run) | 12 s | 7 à 8 s par tâche, `setup-uv` 1 s |
| Étape 2a : cache chaud | 14 s | 11 s par tâche, `setup-uv` 3 s |
| Étape 2b : matrice Python 3.12 / 3.13 / 3.14 sur test | 19 s | 9 à 12 s par tâche |
| Étape 3 : artefact de couverture | 18 s | 8 à 14 s par tâche |

Les trois tâches démarrent à la même seconde : la durée totale suit la tâche la plus lente, pas la somme des tâches.

### Où passe le temps ?

Presque tout part dans les frais fixes de chaque tâche : démarrage de la machine, checkout, installation de uv. Les 14 tests eux-mêmes s'exécutent en moins d'une seconde, et `uv sync` prend environ 1 s. Les écarts de quelques secondes d'un run à l'autre viennent surtout de la machine attribuée (`build` a varié de 7 à 12 s avec le même cache) : c'est le journal qui fait foi, pas le chronomètre.

### Le cache

`setup-uv` active déjà le cache par défaut (`enable-cache: "auto"`), et une branche peut lire le cache de `main` : le premier run « froid » avait donc déjà un cache hérité du TD 1. Après suppression du cache, la mesure montre que le cache chaud est plus lent que le froid : restaurer 44 Mo prend plus de temps que laisser uv télécharger les quelques dépendances du projet. On garde `enable-cache: true` écrit explicitement pour documenter l'intention et ne pas dépendre d'un changement de valeur par défaut, mais sur ce projet il ne fait pas gagner de temps.

### Pourquoi la matrice sur test et pas sur lint ?

Les tests exécutent le code, et son comportement peut changer d'une version de Python à l'autre. Le lint, lui, analyse le code sans l'exécuter : ruff donne le même résultat quelle que soit la version de l'interpréteur. Le lancer trois fois coûterait trois machines pour un seul résultat.

### Que ferions-nous en premier pour accélérer ?

Rien d'urgent : le pipeline reste sous les 20 s. S'il fallait gagner du temps, on commencerait par supprimer ce qui ne sert à rien : le `uv sync` de la tâche `build` (`uv build` n'a pas besoin des dépendances installées) et le cache, tant que les dépendances s'installent en une seconde. Découper davantage en tâches ne ferait qu'ajouter des frais fixes de démarrage.
