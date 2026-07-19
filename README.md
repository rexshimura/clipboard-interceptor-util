# CARUT // Clipboard Auto-Redirector Utility

![License](https://img.shields.io/badge/license-MIT-bd4646?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%20x64-bd4646?style=flat-square)
![Status](https://img.shields.io/badge/engine-active-bd4646?style=flat-square)

**CARUT** (Clipboard Auto-Redirector Utility) is a lightweight, background automation engine designed to completely eliminate the tedious steps of manual screenshot saving. 

Instead of opening an image editor, pasting your clipboard content, and navigating directory windows every time you capture a snippet, CARUT silently intercepts new image fragments directly from your system clipboard. It instantly exposes a sleek, custom crimson prompt panel allowing you to assign rapid file prefixes, apply auto-incrementing naming chains, route files to dedicated workspace targets, and drop out of sight in a click.

---

## Core Operational Architecture

*   **Asynchronous Polling Engine:** Operates quietly on a background daemon thread, continuously scanning clipboard layers without hindering native Windows user interface performance.
*   **Smart-Difference Matching:** Implements pixel bounding-box delta checks (`ImageChops.difference`) to guarantee the interactive prompt triggers exclusively for *new* image captures, preventing duplicate file generation loops.
*   **Thread-Safe UI Queuing:** Offloads clipboard monitoring layers to helper worker threads while safely communicating window deployment back to the main GUI event loop thread using absolute execution queues (`.after()`).

---

## Key Operational Systems

*   **Dynamic Auto-Increment Naming:** Tracks sequential saves automatically (`compilation_1`, `compilation_2`) to streamline rapid mass asset collection without manual typing overhead.
*   **Target Routing Controls:** Instantly alter directory save points and swap file extension wrappers (`.png`, `.jpg`, `.jpeg`) mid-workflow directly inside the active interface panels.
*   **Visual Countdown Terminating Cycle:** Includes a dedicated visual countdown workflow engine built into the persistent micro-widget. Toggling the engine to `OFF` drops active window layouts, executes a localized 3-second countdown visual tracker, unlinks the taskbar icon, and safely shuts down the background python process cleanly.
*   **Aesthetic Cyberpunk UI:** Built with a cohesive borderless dark mode canvas theme (`#121212`), high-contrast crimson highlights (`#bd4646`), retro terminal typography (`Courier New`), and transient, non-stealing topmost focus toast notifications.

---

## Technical Topics Covered

1. **Multi-Threaded UI Orchestration:** Managing asynchronous clipboard loops alongside blocking `pystray` system tray instances and `customtkinter` main windows.
2. **Dynamic Canvas Telemetry:** Translating advanced component rendering architectures into performant, native HTML5 Canvas configurations for web delivery.
3. **Standalone Binary Compilation:** Packaging structural frameworks, font collections, and asset paths into self-contained, single-file executables (`.exe`) via `PyInstaller`.
4. **OS Trust & Code Integrity:** Navigating modern operating system defensive perimeters, identity mapping protocols, and individual validation signature requirements.

---

## Crucial Note for Users (SmartScreen Alert)

Because this executable is newly compiled and unsigned, **Microsoft Defender SmartScreen will throw a purple/blue warning banner** stating *"Windows protected your PC - Unknown Publisher"* when running it for the first time.

**This is normal behavior for indie tools compiled with PyInstaller.** 
To launch the tool:
1. Click **"More Info"** on the Windows warning window.
2. Click the **"Run Anyway"** button that appears.

Once authorized, Windows will remember the configuration, and CARUT will initialize instantly from your system tray on subsequent launches!

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

Developed by **Rexshimura** | 2026