import React from 'react'

const PlaceholderPage: React.FC<{title:string}> = ({title}) => {
  return (
    <div>
      <h2>{title}</h2>
      <div className="card empty">This module is a placeholder. The UI will be connected to the backend later.</div>
    </div>
  )
}

export default PlaceholderPage
