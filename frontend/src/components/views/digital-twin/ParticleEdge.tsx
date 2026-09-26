import React from 'react';
import { BaseEdge, EdgeProps, getSmoothStepPath, EdgeLabelRenderer } from '@xyflow/react';

export interface ParticleEdgeData {
  particleColor?: string;
  particleSpeed?: string; // e.g. '2s'
  particleSize?: number;
  label?: string;
  isAlarm?: boolean;
  isStandby?: boolean;
  flowDirection?: 'forward' | 'reverse' | 'bidirectional';
  powerKw?: string;
  secondaryText?: string;
}

export const ParticleEdge: React.FC<EdgeProps> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  data,
}) => {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  });

  const edgeData = (data || {}) as ParticleEdgeData;
  const particleColor = edgeData.particleColor || '#4648d4';
  const particleSpeed = edgeData.particleSpeed || '2.2s';
  const isAlarm = !!edgeData.isAlarm;
  const isStandby = !!edgeData.isStandby;
  const label = edgeData.label;

  // Unique ID for the SVG path for animateMotion referencing
  const pathId = `path-${id.replace(/[^a-zA-Z0-9-_]/g, '_')}`;

  return (
    <>
      {/* Base Edge Path with subtle background halo for pro depth */}
      <path
        d={edgePath}
        fill="none"
        stroke={isAlarm ? 'rgba(244, 63, 94, 0.15)' : isStandby ? 'transparent' : 'rgba(70, 72, 212, 0.12)'}
        strokeWidth={Number(style.strokeWidth || 2) + 6}
        strokeLinecap="round"
      />

      <BaseEdge 
        id={id} 
        path={edgePath} 
        style={{
          ...style,
          stroke: isAlarm ? '#f43f5e' : isStandby ? '#d4d4d8' : style.stroke || '#4648d4',
          strokeWidth: isAlarm ? 3 : isStandby ? 1.5 : Number(style.strokeWidth || 2),
          strokeDasharray: isStandby ? '5,5' : isAlarm ? '6,3' : style.strokeDasharray,
          transition: 'stroke 0.3s ease, stroke-width 0.3s ease',
        }} 
        markerEnd={markerEnd} 
      />

      {/* Hidden Path definition with ID for SVG animateMotion */}
      <path
        id={pathId}
        d={edgePath}
        fill="none"
        stroke="none"
      />

      {/* Animated Flow Particles when not on standby */}
      {!isStandby && (
        <g className="pointer-events-none">
          {/* Particle 1 */}
          <circle
            r={isAlarm ? 4 : 3}
            fill={isAlarm ? '#e11d48' : particleColor}
            className="filter drop-shadow-[0_0_5px_currentColor]"
          >
            <animateMotion
              dur={isAlarm ? '1.1s' : particleSpeed}
              repeatCount="indefinite"
              begin="0s"
              rotate="auto"
            >
              <mpath href={`#${pathId}`} />
            </animateMotion>
          </circle>

          {/* Particle 2 (Staggered offset) */}
          <circle
            r={isAlarm ? 3 : 2.5}
            fill={isAlarm ? '#f43f5e' : particleColor}
            opacity={0.8}
            className="filter drop-shadow-[0_0_4px_currentColor]"
          >
            <animateMotion
              dur={isAlarm ? '1.1s' : particleSpeed}
              repeatCount="indefinite"
              begin={isAlarm ? '0.55s' : '1.1s'}
              rotate="auto"
            >
              <mpath href={`#${pathId}`} />
            </animateMotion>
          </circle>

          {/* Particle 3 (Trailing tail pulse) */}
          <circle
            r={2}
            fill={isAlarm ? '#fda4af' : particleColor}
            opacity={0.6}
          >
            <animateMotion
              dur={isAlarm ? '1.1s' : particleSpeed}
              repeatCount="indefinite"
              begin={isAlarm ? '0.8s' : '1.65s'}
              rotate="auto"
            >
              <mpath href={`#${pathId}`} />
            </animateMotion>
          </circle>
        </g>
      )}

      {/* Edge Telemetry Label Badge (React Flow Pro style) */}
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
            }}
            className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold tracking-tight shadow-2xs border select-none transition-all duration-200 ${
              isAlarm
                ? 'bg-[#fff1f2] text-[#e11d48] border-[#f43f5e]/40 ring-2 ring-[#f43f5e]/15 animate-pulse'
                : isStandby
                ? 'bg-[#f4f4f5] text-[#71717a] border-[#eaebf0]'
                : 'bg-white/95 text-[#4648d4] border-[#eaebf0] hover:border-[#4648d4]/50 hover:shadow-xs'
            }`}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};
