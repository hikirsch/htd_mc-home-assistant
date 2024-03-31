# HTD MC/MCA-66 Series integration for Home Assistant

This integration will add the HTD MC/MCA-66 Whole House Audio into Home Assistant. This integration depends on 

## Installation steps

### Via HACS (Home Assistant Community Store)

Easiest install is via [HACS](https://hacs.xyz/):

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hikirsch&repository=htd_mc-home-assistant&category=integration)

`HACS -> Integrations -> Explore & Add Repositories -> HTD MC/MCA-66 Series`

### Manually

1. Download the 4 files (`__init__.py`, `htd_mc.py`, `media_player.py`, `manifest.json`) from this repo and place them into your `custom_components/htd_mc` folder.
2. Update your configuration.yaml to include the following (NOTE: Only host is required).
    ```yaml
    htd_mc:
      - host: 192.168.1.123
        port: 10006
        zones:
          - Kitchen
          - Dining Room
          - Living Room
        sources:
          - Chrome Cast
          - FM/AM
      - host: 192.168.xxx.xxx
    ```
3. Restart Home Assistant


## ChangeLog
- April 6, 2020 - Initial release
- April 7, 2020 - Changed Icon and added unique_id (allows editing name and entity ID in Home Assistant UI)
- April 8, 2020 - Support multiple MCAs
- July 18, 2021 - Add version in manifest.json to support 2021.6+
- March 31, 2024 - Upgrading to support HASS 2024.1.0. Adding support for HACS.

## Code Credits
- https://github.com/whitingj/mca66
- https://github.com/steve28/mca66
- http://www.brandonclaps.com/?p=173
