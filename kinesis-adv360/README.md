# kinesis-adv360

My keymap for the Kinesis Advantage360 Pro, kept here so my home and office keyboards stay identical.

## Files

- **keymap.json** is the source of truth. It was read off the keyboard through [Kinesis Clique](https://clique.kinesis-ergo.com/), which is built on ZMK Studio. Each layer lists 76 bindings in ZMK key-position order. The `zmk` field is the decoded binding, and `behavior`/`param1`/`param2` are the raw ZMK Studio values.
- **README.md** shows the same keymap as tables, for a quick look.

## Applying it to another keyboard

Clique has no import or export button. To make a second keyboard match, open Clique with that keyboard connected and set each key that differs from these tables, then click Save.

To unlock the keyboard for Clique, press the key bound to `&studio_unlock`, which is on the Mod layer.

## Keymap

Legend: `▽` means transparent (falls through to the layer below) and `·` means no action. `LG(x)` means GUI+x, `LA(x)` means Alt+x, and `LS(x)` means Shift+x. `&tog 1` toggles the keypad layer, `&mo N` holds layer N, and `KP_N1` through `KP_N4` are keypad keys.

### Layer: Base

| Row | Left hand | Thumb cluster | Right hand |
|---|---|---|---|
| Number row | `ESC` `N1` `N2` `N3` `N4` `N5` `&tog 1` | — | `&mo 3` `N6` `N7` `N8` `N9` `N0` `MINUS` |
| Top row | `TAB` `Q` `W` `E` `R` `T` `KP_N1` | — | `KP_N3` `Y` `U` `I` `O` `P` `BSLH` |
| Home row | `ESC` `A` `S` `D` `F` `G` `KP_N2` | `LGUI` `LALT` `LALT` `RGUI` | `KP_N4` `H` `J` `K` `L` `SEMI` `SQT` |
| Bottom row | `SPACE` `Z` `X` `C` `V` `B` | `LG(TAB)` `LCTRL` | `N` `M` `COMMA` `DOT` `FSLH` `N1` |
| Edge row + thumbs | `&mo 2` `GRAVE` `EQUAL` `LEFT` `RIGHT` | `BSPC` `LSHFT` `LG(GRAVE)` `LA(LGUI)` `RET` `SPACE` | `UP` `DOWN` `LBKT` `RBKT` `&mo 2` |

### Layer: Kp

| Row | Left hand | Thumb cluster | Right hand |
|---|---|---|---|
| Number row | `▽` `▽` `▽` `▽` `▽` `▽` `▽` | — | `▽` `▽` `▽` `▽` `▽` `▽` `▽` |
| Top row | `▽` `▽` `▽` `LS(N9)` `LS(N0)` `▽` `▽` | — | `▽` `▽` `▽` `UP` `▽` `▽` `▽` |
| Home row | `▽` `▽` `LBKT` `RBKT` `LS(LBKT)` `LS(RBKT)` `▽` | `▽` `▽` `▽` `▽` | `▽` `▽` `LEFT` `DOWN` `RIGHT` `▽` `▽` |
| Bottom row | `▽` `▽` `▽` `▽` `▽` `▽` | `▽` `▽` | `▽` `▽` `▽` `▽` `▽` `▽` |
| Edge row + thumbs | `▽` `▽` `▽` `▽` `▽` | `▽` `▽` `▽` `▽` `▽` `▽` | `▽` `▽` `▽` `▽` `▽` |

### Layer: Fn

| Row | Left hand | Thumb cluster | Right hand |
|---|---|---|---|
| Number row | `F1` `F2` `F3` `F4` `F5` `F6` `&tog 1` | — | `&mo 3` `F7` `F8` `F9` `F10` `F11` `F12` |
| Top row | `▽` `▽` `▽` `▽` `▽` `▽` `·` | — | `·` `▽` `▽` `▽` `▽` `▽` `▽` |
| Home row | `▽` `▽` `▽` `▽` `▽` `▽` `·` | `▽` `▽` `▽` `▽` | `·` `▽` `▽` `▽` `▽` `▽` `▽` |
| Bottom row | `▽` `▽` `▽` `▽` `▽` `▽` | `▽` `▽` | `▽` `▽` `▽` `▽` `▽` `▽` |
| Edge row + thumbs | `▽` `▽` `▽` `▽` `▽` | `▽` `▽` `▽` `▽` `▽` `▽` | `▽` `▽` `▽` `▽` `▽` |

### Layer: Mod

| Row | Left hand | Thumb cluster | Right hand |
|---|---|---|---|
| Number row | `·` `&bt BT_SEL 0` `&bt BT_SEL 1` `&bt BT_SEL 2` `&bt BT_SEL 3` `&bt BT_SEL 4` `·` | — | `▽` `·` `·` `·` `·` `·` `·` |
| Top row | `·` `·` `·` `·` `·` `·` `&bootloader` | — | `&bootloader` `·` `·` `·` `·` `·` `·` |
| Home row | `&studio_unlock` `·` `·` `·` `·` `·` `·` | `·` `·` `&bt BT_CLR` `·` | `Battery Level` `·` `·` `·` `·` `·` `·` |
| Bottom row | `·` `·` `·` `·` `macro_ver` `·` | `·` `·` | `·` `·` `·` `·` `·` `·` |
| Edge row + thumbs | `·` `·` `·` `·` `·` | `·` `·` `·` `·` `&bl BL_TOG` `&rgb_ug RGB_TOG` | `&bl BL_INC` `&bl BL_DEC` `·` `·` `·` |
