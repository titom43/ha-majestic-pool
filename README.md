# Majestic Pool

Intégration Home Assistant (Custom Component) pour piloter un coffret **Majestic** via Bluetooth Low Energy (BLE).

> Statut: projet communautaire en cours de finalisation du workflow d'appairage avancé.

## Fonctionnalités

- Connexion BLE au coffret Majestic.
- Encodage/décodage du protocole paquet `:<size><cmd><payload><crc>`.
- Capteur température d'eau (`sensor.water_temperature`).
- Switches configurables (`switch`) pour piloter des équipements (pompe, éclairage, etc.).
- Capteurs de valeur configurables (`sensor`) extraits des payloads BLE.
- Capteurs diagnostics bruts (payload hex) pour commandes de polling.
- Boutons d'actions brutes configurables.
- Services Home Assistant pour envoi de commandes brutes et refresh.
- Mode connexion BLE à la demande pour limiter l'impact sur le boîtier physique.

## Prérequis

- Home Assistant `2024.8.0+`
- HACS installé
- Coffret Majestic à portée BLE

## Installation via HACS

1. Ouvrir HACS -> `Integrations` -> menu `...` -> `Custom repositories`.
2. Ajouter ce dépôt: `https://github.com/titom43/ha-majestic-pool`.
3. Catégorie: `Integration`.
4. Installer `Majestic Pool`.
5. Redémarrer Home Assistant.
6. Aller dans `Paramètres` -> `Appareils et services` -> `Ajouter une intégration` -> `Majestic Pool`.

## Configuration (UI)

### Champs principaux

- `address`: adresse MAC BLE du boîtier
- `poll_interval`: fréquence de polling (secondes)
- `temperature_command`: commande de lecture température (défaut `0x22`)
- `enable_temperature_poll`: active/désactive le polling périodique
- `connect_on_demand`: se connecte uniquement pour action/poll puis se déconnecte

### Actions brutes

Champ `action_commands`:

`Label:cmd_hex[:payload_hex],Label2:7a`

Exemples (préremplis par défaut):
- `Projecteur toggle:23`
- `Pompe manuel:35`
- `Pompe auto:36`
- `Pompe boost:37`

### Switches configurables

Champ `switch_definitions`:

`Label|on_cmd|on_payload|off_cmd|off_payload|state_cmd|on_value`

Exemples (préremplis par défaut):
- `Projecteur|23||23|||`
- `Pompe Auto|36||35|||`

Notes:
- `state_cmd` et `on_value` sont optionnels.
- Sans `state_cmd/on_value`, le switch fonctionne en `assumed_state`.

### Value sensors configurables

Champ `value_sensor_definitions`:

`Label|cmd|byte_index|scale`

Exemples (préremplis par défaut):
- `Courant pompe|27|0|0.1`
- `Courant booster|27|1|0.1`

### Commandes diagnostics

Champ `diagnostic_commands` (liste hex):

`2d,27,03,04,64,6e`

## Services Home Assistant

### `majestic_pool.send_command`

- `entry_id` (optionnel)
- `command` (0..255)
- `payload` (optionnel, hex string ou liste d'octets)

### `majestic_pool.refresh`

- `entry_id` (optionnel)

## Informations protocole BLE connues

- Service UART: `569a1101-b87f-490c-92cb-11ba5ea5167c`
- RX notify: `569a2000-b87f-490c-92cb-11ba5ea5167c`
- TX write: `569a2001-b87f-490c-92cb-11ba5ea5167c`
- Pairing characteristic (à intégrer complètement): `569a2004-b87f-490c-92cb-11ba5ea5167c`
- CRC: `((sum(bytes) & 0xFF) ^ 0xFF) + 1`

## Mapping commandes (actuel)

- `0x23`: toggle projecteur
- `0x35`: pompe manuel
- `0x36`: pompe auto
- `0x37`: pompe boost
- `0x2d`: lecture statut pompe
- `0x27`: lecture courants pompe/booster
- `0x22`: lecture température

## Limites actuelles

- Le workflow d'appairage avancé (manip physique + séquence BLE spécifique) n'est pas encore entièrement automatisé côté intégration.
- L'échelle exacte des courants (`A`, `0.1A`, etc.) reste à confirmer définitivement selon captures terrain.

## Support / Contribution

- Issues / améliorations: `https://github.com/titom43/ha-majestic-pool/issues`
- PR bienvenues.
