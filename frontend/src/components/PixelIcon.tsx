/**
 * Renders a pixel grid as crisp 1px-per-cell SVG.
 *
 * Lives apart from the grids themselves (dashIcons.ts) so this file exports
 * only a component - a module that exports both a component and constants
 * loses fast refresh.
 */

interface Props {
  /** A grid from dashIcons.ts: rows of "#" (on) and "." (off). */
  grid: string;
  className?: string;
}

export function PixelIcon({ grid, className }: Props) {
  const rows = grid.trim().split("\n");
  const height = rows.length;
  const width = rows[0].length;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      shapeRendering="crispEdges"
      fill="currentColor"
      aria-hidden="true"
      className={className}
    >
      {rows.map((row, y) =>
        [...row].map((cell, x) =>
          cell === "#" ? (
            <rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" />
          ) : null,
        ),
      )}
    </svg>
  );
}
