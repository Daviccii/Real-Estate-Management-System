import RoleUsers from './RoleUsers'

const AgentsManagement: React.FC = () => {
  return (
    <RoleUsers 
      role="agent"
      title="Agents Management"
      description="Manage real estate agents who list and sell properties."
    />
  )
}

export default AgentsManagement