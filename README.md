# Majestic Pool (HACS)

Integration Home Assistant (custom component HACS) pour piloter un coffret Majestic via BLE.

## Ce qui est inclus

- Connexion BLE sur les UUIDs Majestic connus.
- Encodage/décodage du protocole `:<size><cmd><payload><crc>`.
- Capteur `sensor.water_temperature` (commande par défaut `0x02`).
- Capteurs diagnostics bruts (désactivés par défaut) pour `cmd 0x03/0x04/0x64/0x6e`.
- Boutons d'action configurables.
- Services pour envoyer des commandes brutes.

## Installation (HACS)

1. Ajouter ce dépôt dans HACS (Custom repositories, catégorie `Integration`).
2. Installer `Majestic Pool`.
3. Redémarrer Home Assistant.
4. Ajouter l'intégration via l'UI.

## Configuration actions

Champ `action_commands`:

`Label:cmd_hex[:payload_hex],Label2:7a,Freeze On:40:01`

Exemples:
- `Light Toggle:33`
- `Pump Boost:41`
- `Freeze On:50:01`
- `Freeze Off:50:00`

## Services

- `majestic_pool.send_command`
  - `command` (0..255)
  - `payload` (hex string, ex `0102ff`, ou liste d'octets)
  - `entry_id` (optionnel)
- `majestic_pool.refresh`
  - `entry_id` (optionnel)

## Notes reverse-engineering

- Service BLE: `569a1101-b87f-490c-92cb-11ba5ea5167c`
- RX notify: `569a2000-b87f-490c-92cb-11ba5ea5167c`
- TX write: `569a2001-b87f-490c-92cb-11ba5ea5167c`
- CRC: `((sum(bytes) & 0xFF) ^ 0xFF) + 1`

Le mapping complet `commande -> action` peut encore être affiné au fur et à mesure des captures/appuis dans l'app officielle.

## Avancement Ghidra

L'analyse de `KKTO_MAJESTIC_uncompressed.dll` confirme des méthodes IL nommées :
- `CommandGetProgramModeAndShutter`
- `CommandGetTemperatures`
- `CommandGetLightParameters`
- `CommandGetRfStatus`
- `CommandGetWarning`

Le pcap fourni montre le cycle de polling :
- `:0303FA` (`cmd=0x03`)
- `:0302FB` (`cmd=0x02`)
- `:0304F9` (`cmd=0x04`)
- `:036499` (`cmd=0x64`)
- `:036E8F` (`cmd=0x6e`)
