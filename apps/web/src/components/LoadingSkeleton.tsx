import React from 'react';

interface LoadingSkeletonProps {
  lines?: number;
  height?: number | string;
  style?: React.CSSProperties;
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({
  lines = 3,
  height = '16px',
  style,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '12px',
        width: '100%',
        ...style,
      }}
    >
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-shimmer"
          style={{
            height,
            width: i === lines - 1 && lines > 1 ? '70%' : '100%',
            borderRadius: '4px',
          }}
        />
      ))}
    </div>
  );
};

