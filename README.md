<a href="https://krisskira.github.io/smd-soldering-hotplate/">
  <img src="landing-page/public/media/og-cover.jpg" alt="HotPlate: a real HEAT cycle, with HotPanel and the temperature curve" width="100%" />
</a>

# HotPlate

An open SMD reflow station. Instead of heating by eye, it runs a **Soldering Profile**: a precise temperature curve, step by step. It ramps under control, holds each plateau for the right time, signals when it is done and cools down on its own.

[Site](https://krisskira.github.io/smd-soldering-hotplate/) · [HotPanel and Studio](#two-ways-to-run-it) · [Docs](docs/README.md) · [Email](mailto:krisskira@gmail.com) · [Leer en español](README.es.md)

## What it does

- **HEAT** runs the whole profile from one gesture: optional wait, preheat, up to four rising or flat steps, then cooldown.
- **Scheduled start** waits from 00:00 (immediate) up to 12:00 before the cycle begins.
- **Predictive PI** cuts power before the target, so the plate's own inertia does not overshoot.
- **Autotune**, launched from HotPlate Studio, learns how the plate responds and stores the gains.
- **Safety** keeps the heater off at boot. A sensor fault or a reading above `temp_max_c` cuts the output at once.

## Two ways to run it

- **HotPanel**, the onboard interface: a large temperature, two tiles and a knob. Turn to choose, press to confirm. Heat starts or stops the cycle. Settings edits the four steps and the wait clock.
- **HotPlate Studio**, the desktop app over USB: live temperature chart, profile editing, CSV export, autotune and the limits the panel does not expose. When Studio takes control, HotPanel shows **USB** and local input locks. The two modes never run together.

## What's in the repo

- [`firmware/avr/`](firmware/avr/) — ATmega16 firmware at 8 MHz. The map of docs and code starts at [product features](firmware/avr/doc/product_features.md), [program flows](firmware/avr/doc/program_flows.md) and [architecture](firmware/avr/doc/architecture.md).
- [`hotplate-studio/`](hotplate-studio/) — HotPlate Studio (Python). The screens it follows are in [`hotplate-studio/design/`](hotplate-studio/design/).
- [`hardware/`](hardware/) — KiCad board and datasheets.
- [`mechanical/`](mechanical/) — 3D enclosure, covers and knob.
- [`landing-page/`](landing-page/) — the public site, React and TypeScript on Vite.

Flash is 16 KB. Thermal control, safety and the approved UI come first. See the [feature budget](firmware/avr/doc/feature_budget.md).

## Build

```bash
cd firmware/avr && make clean && make && make size && make usb-host-test

cd hotplate-studio && pip install -r requirements.txt && python app.py

cd landing-page && npm install && npm run dev
```

The site publishes to GitHub Pages from `.github/workflows/pages.yml` on every push to `main` that touches `landing-page/`. In the repository: **Settings → Pages → Source: GitHub Actions**.

## License

Open hardware and software. Use, study, modify and share it at your own risk. It works with mains power and high temperatures.

| What | License |
|------|---------|
| Firmware and HotPlate Studio | [MIT](LICENSE) |
| Board and 3D models | [CERN-OHL-P-2.0](LICENSE) |
| Docs and icons | [CC BY 4.0](LICENSE) |

The full text is in [LICENSE](LICENSE).

Author: **Crhistian David Vergara Gómez** · **krisskira@gmail.com**
