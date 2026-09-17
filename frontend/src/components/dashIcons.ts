/**
 * Dashboard tell-tale pictograms, drawn as pixel grids.
 *
 * Emoji and icon fonts both render smooth and colourful, which would be the
 * only anti-aliased thing on screen. These are plotted on a 9x9 grid and
 * emitted as 1x1 SVG rects with crisp edges instead, so they look etched into
 * the plastic next to the art.
 *
 * Each one pairs with the engraved word under its dial in RadarPanel. They
 * read, in order: how much money he thinks you have, how much standing (he
 * notices a good watch before he notices you), how much of your story he
 * believes, and what he expects to be handed at the end.
 */

/*
 * Every grid is exactly 9x9 and gets drawn into a box that is a whole
 * multiple of 9 px, so each cell lands on real pixels. A 7-wide grid or an
 * awkward box size puts the edges on half pixels and the icon turns to mush.
 */

/** Money - the plain dollar sign. */
const MONEY = `
....#....
..#####..
.#..#..#.
.#..#....
..#####..
....#..#.
.#..#..#.
..#####..
....#....
`;

/** A good watch. He notices the watch before he notices you. */
const STATUS = `
...###...
...###...
.#######.
.#.....#.
.#..#..#.
.#..##.#.
.#.....#.
.#######.
...###...
`;

/*
 * The rear-view mirror on its stem - he is checking it again.
 *
 * This was an eye first, but a round outline with a square pupil reads as a
 * record button at this size. The mirror is unmistakable as a silhouette and
 * says the same thing, in a language the rest of the dashboard already speaks.
 */
const SUSPICION = `
....#....
...###...
#########
#.......#
#.##....#
#.......#
#########
.........
.........
`;

/** An open palm, waiting. */
const TIP = `
..#.#.#..
..#.#.#..
..#####..
.######..
#######..
#######..
.#####...
..###....
.........
`;

export const DASH_ICON = {
  money: MONEY,
  status: STATUS,
  suspicion: SUSPICION,
  tip: TIP,
} as const;

