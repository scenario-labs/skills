// spec.js: TOUR, a 52 s reference film on a 172 BPM grid that uses 13 of the 14 blocks with most of their options
// (Picture is in kaiju-postal). Copy the block you need from here. The copy is placeholder text and logo.svg a placeholder mark: replace both.
// No music ships with it: generate a bed (the skill's references/sound.md), then set music.offset from beat_grid.py.
import { Words, Strike, Graph, Hero, Prompt, Stretch, Fly, Notes, Counters, Progress, Chain, Rewind, Logo } from './blocks.js';

const BRIEF = [['A 30-second teaser for a '], ['night market', 1], [': paper lanterns, '], ['street food', 1], [', a '], ['brass band', 1], [' on the drop and the '], ['name', 1], [' on the last hit.']];
const chars = BRIEF.reduce((n, [s]) => n + s.length, 0);

export default {
  title: 'Tour',
  bpm: 172, beats: 150, fps: 60,
  palette: { bg: '#0A0F14', paper: '#F1F4F2', accent: '#2BD9A8', hot: '#12B886', ink: '#0F1412' },
  hud: 'TOUR  ·  EVERY BLOCK', hudOut: [146, 148],
  logo: 'logo.svg',
  music: { file: 'audio/music.mp3', offset: 0, stopBeat: 140 },

  scenes: [
    // 1. Words: a point charges, then one idea per beat; split carries a code backdrop, a scramble, a glitch and a note.
    [Words, 0, 9, { charge: true, shots: [
      { at: 1, style: 'punch3d', text: 'FOURTEEN', fx: 'punch' },
      { at: 2, style: 'slam', text: 'BLOCKS', ground: 'accent' },
      { at: 3, style: 'stack', text: ['ONE', 'SPEC'], ground: 'paper', in: 'whipX', fx: 'none' },
      { at: 4.5, style: 'split', text: ['SET TO', 'SOUND.'], in: 'whipY', fx: 'punch', big: true, code: true, scramble: [2.1, 3.6], glitch: 2.5, note: '// spec.js · scenes', noteAt: 1.5 },
    ], exit: { type: 'zoom', at: 8.1, char: 1 } }],

    // 2. Strike: three denials over the three mocks (timeline, tiles, rack).
    [Strike, 9, 19, { items: [
      { at: 9, word: 'GUESSWORK.', ui: { type: 'timeline', title: 'cut_guess_v7', tag: 'GUESSING  12%' } },
      { at: 12, word: 'PRESETS.', ground: 'paper', ui: { type: 'tiles', tiles: [['BLUR', '◆', 'PRESET 01'], ['SHAKE', '●', 'PRESET 02'], ['WIPE', '▲', 'PRESET 03'], ['ZOOM', '■', 'PRESET 04'], ['GLOW', '◆', 'PRESET 05'], ['SPIN', '●', 'PRESET 06'], ['FADE', '▲', 'PRESET 07'], ['TRAIL', '■', 'PRESET 08']] } },
      { at: 15, word: 'QUEUE.', ui: { type: 'rack', rows: ['QUEUE 01', 'QUEUE 02', 'QUEUE 03'] } },
    ] }],

    // 3. Graph: the camera rides the comet, then flies through the 0.
    [Graph, 19, 25, { number: '0', label: 'CUTS', sub: 'OFF THE BEAT' }],

    // 4. Hero: a kicker, then the extruded title.
    [Hero, 25, 33, { kicker: 'THIS IS', title: 'THE TOUR.', sub: 'a walk through the blocks', whipOut: [0, 1150, .13] }],

    // 5. Prompt: a brief types itself; the push into Enter is the drop.
    [Prompt, 33, 52, { label: 'BRIEF.md', text: BRIEF }],

    // 6-8. Stretch, Fly, and a run of beat cuts that accelerates into a flash.
    [Stretch, 52, 60, { word: 'BOUNCE.', whipOut: [1800, 0, .14, -3] }],
    [Fly, 60, 71, { words: [['INTO', 'paper'], ['THE', 'accent'], ['DEEP', 'paper'], ['END.', 'accent']] }],
    [Words, 71, 77, { shots: [
      { at: 71, style: 'cut', text: 'ONE.', color: 'paper', size: 380, rot: -3, fx: 'beat' },
      { at: 72, style: 'cut', text: 'TWO.', ground: 'accent', size: 560, rot: 4, fx: 'beat' },
      { at: 73, style: 'cut', text: 'THREE.', color: 'accent', size: 380, wdth: 118, rot: -2, fx: 'beat' },
      { at: 74, style: 'cut', text: 'FOUR.', ground: 'paper', size: 440, fx: 'beat' },
      { at: 74.5, style: 'cut', text: 'AND', color: 'accent', size: 300, rot: 8, dy: -140, fx: 'beat' },
      { at: 75, style: 'cut', text: 'ONE.', ground: 'accent', size: 540, rot: -6, dy: 20, fx: 'beat' },
      { at: 75.5, style: 'cut', text: 'TWO.', ground: 'paper', size: 380, rot: 3, stroke: 4, fx: 'beat' },
      { at: 75.75, style: 'cut', text: 'GO.', color: 'paper', size: 620, rot: -4, rgb: true, fx: 'beat' },
    ], exit: { type: 'flash', at: 76 } }],

    // 9. Notes: three notes typed into a panel, each one played on the preview.
    [Notes, 77, 93, { preview: 'BOUNCE.', tag: 'PREVIEW  ·  00:21', file: 'spec.js', notes: [['make it warmer', 'recolor'], ['shorter opening', 'trim'], ['louder on the hits', 'punch']] }],

    // 10-11. Counters on slot reels over the film's own source, then Progress past a render head.
    [Counters, 93, 104, { title: 'tour / spec.js', counters: [['14', 'BLOCKS'], ['{lines}', 'LINES OF SOURCE'], ['{frames}', 'FRAMES RENDERED']], whipOut: [1700, 0, .13, 2] }],
    [Progress, 104, 113, { lines: ['DRAWN', 'FRAME BY FRAME.'], doneRight: 'FRAME BY FRAME', whipOut: [1700, 0, .13, -2],
      cards: [['FOURTEEN', 'bg', 'paper'], ['BLOCKS', 'accent', 'ink'], ['ONE', 'paper', 'ink'], ['SPEC', 'bg', 'accent'], ['NO', 'bg', 'accent'], ['0', 'paper', 'ink'], ['TOUR.', 'bg', 'paper'], ['BOUNCE.', 'accent', 'ink'], ['DEEP', 'bg', 'accent'], ['ONE.', 'bg', 'paper'], ['GO.', 'paper', 'ink'], ['TWO.', 'accent', 'ink'], ['SOUND.', 'bg', 'accent'], ['SPEC.', 'accent', 'ink']] }],

    // 12. Chain: three nodes 2,000 px apart, linked by the comet.
    [Chain, 113, 125, { nodes: [['BRIEF', `brief.md · ${chars} chars`], ['BEATS', '{seconds} s on the grid'], ['FILM.', '4K · 60 FPS · {frames} frames']], whipOut: [0, -1100, .13] }],

    // 13. Rewind: the film so far, backwards inside a playback window.
    [Rewind, 125, 133, { label: 'REPLAY' }],

    // 14. Words again, ending in a collapse to the point the logo line grows from.
    [Words, 133, 140, { shots: [
      { at: 133, style: 'pair', text: ['ALL', 'FOURTEEN.'], fx: 'beat', cue: 'impact', gain: .7 },
      { at: 135, style: 'slam', text: 'ONE', ground: 'accent', size: 540, wdth: 110, echo: false, in: 'whipY', fx: 'beat' },
      { at: 136, style: 'slam', text: 'SPEC.', ground: 'paper', size: 440, wdth: 104, dot: true, from: 1.8, fx: 'punch', big: true, glyphs: true, scramble: [1, 2], inverts: [1, 1.5], flip: { at: 2, ground: 'bg', color: 'paper' } },
    ], exit: { type: 'collapse', at: 138.2, end: 139.6 } }],

    // 15. Logo: the four marks of logo.svg drop in, then its bar wipes on. The music stops on beat 140.
    [Logo, 139, 150, { mark: ['m1', 'm2', 'm3', 'm4'], word: ['w1'], tagline: 'Fourteen blocks. One spec.', small: 'A TOUR OF THE ENGINE' }],
  ],

  // the caption line, top left: [startBeat, endBeat, [[word, beat], ...]]
  captions: [
    [0, 8.6, [['Fourteen', 1], ['blocks,', 2], ['one', 3], ['spec,', 3.5], ['set', 4.6], ['to', 4.8], ['sound.', 5]]],
    [9, 18.8, [['No', 10], ['guesswork.', 10.4], ['No', 13], ['presets.', 13.4], ['No', 16.5], ['queue.', 16.9]]],
    [19, 24.6, [['Zero', 19.2], ['cuts', 19.8], ['off', 20.4], ['the', 21], ['beat.', 21.6]]],
    [25, 32.5, [['This', 25.2], ['is', 26.2], ['the', 27], ['tour.', 28.6]]],
    [33, 49.2, [['Start', 33.3], ['from', 33.9], ['a', 34.5], ['brief.', 35.2]]],
    [52, 59.4, [['Type', 52.1], ['that', 53], ['bends', 53.6], ['on', 54.8], ['its', 55.2], ['width', 55.6], ['axis.', 56.8]]],
    [60, 70.5, [['Fly', 60.2], ['into', 60.8], ['the', 62], ['deep', 62.7], ['end.', 63.6]]],
    [71, 76.4, [['And', 71], ['count', 71.4], ['it', 71.8], ['in.', 72.4]]],
    [77, 92.4, [['Feedback', 77.3], ['in', 78.6], ['plain', 79.2], ['words.', 79.8]]],
    [93, 103.4, [['Fourteen', 93.3], ['blocks,', 93.9], ['counted.', 94.6]]],
    [104, 112.4, [['Drawn', 104.3], ['frame', 105.1], ['by', 105.4], ['frame.', 105.7]]],
    [113, 124.4, [['Brief,', 113.6], ['beats,', 114.2], ['film.', 117.6]]],
    [125, 132.4, [['Run', 125.2], ['it', 126.6], ['back.', 127.2]]],
    [133, 138.2, [['All', 133], ['fourteen.', 133.5], ['One', 135], ['spec.', 136]]],
  ],
};
