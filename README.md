# Crumb's Picnic Run

A little toast named Crumb runs, hops and stomps through four levels to reach the picnic and rescue a friend from the Grand Chili.

```powershell
uv run crumb
```

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

## Notes

- Settings and your best score are saved to `%APPDATA%\CrumbsPicnicRun\save.json`.
- The art is drawn with cairo, and the music is generated live with numpy and played through sounddevice.
- Fonts: Bagel Fat One and Sniglet (SIL Open Font License), Luckiest Guy (Apache 2.0). Licences are in `src/crumb/assets/fonts`.
