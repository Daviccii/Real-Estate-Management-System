import React from 'react'

const Skeleton: React.FC<{width?:string|number;height?:string|number,style?:React.CSSProperties}> = ({ width='100%', height=16, style }) => {
  return <div className="skeleton" style={{width, height, borderRadius:6, ...style}} />
}

export default Skeleton
