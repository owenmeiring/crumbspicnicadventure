# Crumb's Picnic Run

A little toast named Crumb runs, hops and stomps through World 1's nine stages to reach the picnic and rescue a friend from the Grand Chili.

```powershell
uv run crumb
```

## World 1

| Stage | Name | |
|---|---|---|
| 1-1 | Picnic Lawn | |
| 1-2 | Cellar Pantry | |
| 1-3 | High Picnic | checkpoint |
| 1-4 | Honeycomb Hollow | |
| 1-5 | Frosted Peaks | |
| 1-6 | Fudge Mines | checkpoint |
| 1-7 | Melon Grove | |
| 1-8 | Sundae Skies | checkpoint |
| 1-9 | Boss Kitchen | the Grand Chili |

If you lose all your lives you can continue from the last checkpoint stage you reached, and Start Game offers to continue from it next time. Stages 1-4 onward are long and hard, with toothpick spikes (they hurt, then put you back on the last safe ledge), crackers that crumble under you, and jelly pads that bounce you high (ground-pound onto one for a super bounce).

## Controls

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | Arrows or A / D | Left stick or D-pad |
| Jump (hold for higher, hold in the air to float) | Space, W or Up | A |
| Run | Shift or Z | RB, LB, Y or a trigger |
| Crouch / ground pound in the air | Down or S | Down |
| Throw fire cookie | F or X | X |
| Roll dodge | E | B |
| Pause | Esc or P | Start |
| Fullscreen | F11 or Alt+Enter | |

Wall slide by pushing into a wall in mid-air, then jump to wall jump. Tap G five times for the level-select dev menu.

## Level builder

Choose **Level Builder** on the title screen. You paint straight onto the live level, with the real art, and press **Play** (or T) to test it instantly. Esc during a test opens the pause menu, which has **Back to editor**.

- **Tools:** ground, brick, ? block (holds a pizza, cookie or coin), stone, dark wall, coins, ants, walnuts, start, goal flag, the Grand Chili and its arena walls, eraser. Keys 1-0, B, V and E select them.
- **Painting:** drag to paint, right-click to erase, Shift+drag to fill a box, Alt+click to pick up whatever's under the cursor.
- **Moving around:** scroll with A / D, the arrows or the mouse wheel; pan with middle-drag or Space+drag; click or drag the minimap to jump.
- **Undo and redo** with Ctrl+Z / Ctrl+Y. Press F1 in the builder for every shortcut.
- **Saving:** Ctrl+S saves the level as a `.json` file in `%APPDATA%\CrumbsPicnicRun\levels`. Your work in progress is also autosaved as a draft.
- **Sharing:** Copy (Ctrl+C) puts the level on the clipboard as JSON and Paste (Ctrl+V) loads one. Levels exported from the original HTML version import as-is.

**Custom Levels** on the title screen lists your saved levels to play, edit or delete, and can import a level from the clipboard.

## Notes

- Settings and your best score are saved to `%APPDATA%\CrumbsPicnicRun\save.json`.
- The art is drawn with cairo, and the music is generated live with numpy and played through sounddevice.
- Fonts: Bagel Fat One and Sniglet (SIL Open Font License), Luckiest Guy (Apache 2.0). Licences are in `src/crumb/assets/fonts`.
