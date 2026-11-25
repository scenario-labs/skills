# GUI paths for expression work

For a person, or a computer-use agent, doing the same steps as `procedures.md` by hand. Menu names
are After Effects 27.0 (macOS shortcuts first, Windows in parentheses).

## Writing and removing expressions

| Task                                         | Path                                                                                                                            |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Add an expression                            | Option-click (Alt-click) the property stopwatch, or Animation > Add Expression (Option+Shift+= / Alt+Shift+=)                   |
| Remove an expression                         | Option-click (Alt-click) the stopwatch again, or Animation > Remove Expression                                                  |
| Link with the pick whip                      | drag the spiral icon next to the expression field onto a property or control                                                    |
| Insert syntax                                | the arrow next to the pick whip opens the Expression Language menu (snippets carry placeholder names that error until replaced) |
| Show only properties with expressions        | select layers, press EE                                                                                                         |
| Enable or disable expressions on many layers | Layer > Switches > Disable Expressions (or the equals-sign switch next to the property)                                         |
| Convert to keyframes (bake)                  | select the property, Animation > Keyframe Assistant > Convert Expression to Keyframes                                           |
| Post-expression curve                        | Graph Editor > Show Post-Expression Graph (bottom bar)                                                                          |

## Controls

| Task                                     | Path                                                                                                                                                               |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Add a control                            | Effect > Expression Controls > Slider, Angle, Checkbox, Color, Point, 3D Point, Layer, Dropdown Menu Control                                                       |
| Edit dropdown items                      | Effect Controls > Dropdown Menu Control > Edit                                                                                                                     |
| Make the controller invisible in renders | Layer > Guide Layer on the controller null                                                                                                                         |
| Expose a control to a parent comp        | drag the property into Window > Essential Graphics, or right-click > Add Property to Essential Graphics; the nested layer then shows it under Essential Properties |

## Errors

| Task                                 | Path                                                                                                                                                      |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Read an error                        | the orange banner at the bottom of the Composition panel; the arrows step through errors, the magnifier reveals the property                              |
| Banner gone for good                 | it was dismissed: Settings (Preferences) > Scripting & Expressions > Show Warning Banner when Project Contains Expression Errors                          |
| Switch the engine for an old project | File > Project Settings > Expressions > Expression Engine (JavaScript or Legacy ExtendScript)                                                             |
| Rename and keep references           | in 27.0 the AI Assistant can rename items and update expression references; a rename by script does not, use `AEX.expressions.renameLayer` (procedures 9) |

## Data footage

| Task                           | Path                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------- |
| Import JSON or CSV             | File > Import > File (`.json`, `.csv`, `.tsv`, `.mgjson`)                             |
| Pick a key with the pick whip  | twirl the data footage layer in a comp, or type `footage("data.json").sourceData.key` |
| Refresh after editing the file | right-click the footage in the Project panel > Reload Footage                         |

## Text style expressions

| Task                                   | Path                                                                               |
| -------------------------------------- | ---------------------------------------------------------------------------------- |
| Find a font's exact name for `setFont` | Expression Language menu > Text > Font... opens a font picker that writes the name |
| Per-character style                    | expression on Source Text returning `text.sourceText.style.set...()`               |

## Measuring by hand

| Task              | Path                                                                             |
| ----------------- | -------------------------------------------------------------------------------- |
| On-screen readout | a text layer with a Source Text expression returning the value (`Math.round` it) |
| Check a loop seam | Graph Editor with Show Post-Expression Graph on, zoom on the loop point          |
