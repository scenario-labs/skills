// spec.js: a 15 s starter. Replace the words, the palette and the name; keep the shape until it works,
// then change blocks. Every number is a beat (60 / bpm seconds). Blocks and options: the skill's references/blocks.md.
import { Words, Strike, Hero, Logo } from './blocks.js';

export default {
  title: 'Product',                       // REPLACE: the film's name (used for file names)
  bpm: 170, beats: 42, fps: 60,           // set bpm to the music's measured tempo (scripts/beat_grid.py)
  palette: { bg: '#0D0F14', paper: '#F2F0EA', accent: '#3D7BFF', hot: '#1F5BFF', ink: '#12141A' },   // REPLACE: brand colors
  hud: 'PRODUCT  ·  LAUNCH', hudOut: [39, 41],
  // music: { file: 'audio/music.mp3', offset: 0, stopBeat: 32 },   // after beat_grid.py: offset puts the drop where you want it
  sounds: {},
  cues: [],

  scenes: [
    // the hook: a point charges, then one idea per beat
    [Words, 0, 8, { charge: true, shots: [
      { at: 1, style: 'punch3d', text: 'MEET', fx: 'punch' },
      { at: 2, style: 'slam', text: 'THE TOOL', ground: 'accent' },
      { at: 3, style: 'stack', text: ['THAT DOES', 'ONE THING.'], ground: 'paper', in: 'whipX', fx: 'none' },
      { at: 5, style: 'split', text: ['AND DOES IT', 'FAST.'], in: 'whipY', fx: 'punch', big: true },
    ] }],
    // what it replaces
    [Strike, 8, 17, { items: [
      { at: 8, word: 'WAITING.', ui: { type: 'timeline', title: 'export_final_v3', tag: 'EXPORTING  4%' } },
      { at: 11, word: 'PLUGINS.', ground: 'paper', ui: { type: 'tiles', tiles: [['ONE', '◆', 'v1.0'], ['TWO', '●', 'v2.1'], ['THREE', '▲', 'v3.2'], ['FOUR', '■', 'v1.4']] } },
      { at: 14, word: 'SERVERS.', ui: { type: 'rack', rows: ['NODE 01', 'NODE 02', 'NODE 03'] } },
    ] }],
    // the name, in 3D
    [Hero, 17, 25, { kicker: 'INTRODUCING', title: 'PRODUCT', sub: 'one line about what it does', whipOut: [0, 1150, .13] }],
    // three beat cuts, then a flash
    [Words, 25, 31, { shots: [
      { at: 25, style: 'cut', text: 'FAST.', color: 'paper', size: 460, rot: -3, fx: 'beat' },
      { at: 26, style: 'cut', text: 'SIMPLE.', ground: 'accent', size: 420, rot: 4, fx: 'beat' },
      { at: 27, style: 'cut', text: 'YOURS.', ground: 'paper', size: 480, fx: 'beat' },
      { at: 28, style: 'cut', text: 'NOW.', color: 'accent', size: 620, rot: -5, rgb: true, fx: 'beat' },
    ], exit: { type: 'flash', at: 30 } }],
    // the end card; the music stops on its first beat (music.stopBeat = 32)
    [Logo, 31, 42, { wordmark: 'PRODUCT', tagline: 'One line that says what it does.', small: 'AVAILABLE NOW' }],
  ],
  captions: [],
};
