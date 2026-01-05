# TP: Transmission fiabilisée de données (RS232 loopback)

Projet Python 3.11+ pour un TP de transmission fiabilisée sur un seul PC en loopback (TX↔RX).

Fonctionnalités:
- Saisie d'un mot de taille variable (binaire multiple de 8 bits, hex paire, ou texte)
- Sélection du port série et du baudrate (8N1)
- Codage par Reed-Solomon (configurable, option pour l'inhiber, correction jusqu'à 20 erreurs)
- Visualisation du mot codé (hex)
- Envoi sur canal RS232 (loopback) et réception
- Injection d'erreurs manuelle et aléatoire
- Décodage / correction et affichage du résultat et des statistiques
- Tramage: STX | LEN(2) | PAYLOAD | ETX avec resynchronisation

Dépendances (voir `requirements.txt`).

Installation rapide:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Lancement:

```bash
python code.py
```

Remarques:
- Le projet utilise `reedsolo` pour le codage Reed-Solomon (correction d'erreurs par octet).
- Pour tester sur un seul PC, configurez un port série en loopback physique (connectez TX à RX) ou utilisez un pair virtuel (com0com / com2com).

Voir `src/` pour le code source.
