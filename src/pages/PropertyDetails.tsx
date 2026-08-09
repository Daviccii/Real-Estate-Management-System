import React from 'react'
import { useParams } from 'react-router-dom'

const PropertyDetailsPage: React.FC = () => {
  const { id } = useParams()
  return (
    <div>
      <h2>Property {id}</h2>
      <div className="card">Property details will be displayed here and connected to the API.</div>
    </div>
  )
}

export default PropertyDetailsPage
