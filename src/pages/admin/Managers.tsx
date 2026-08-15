import RoleUsers from './RoleUsers'

const ManagersManagement: React.FC = () => {
  return (
    <RoleUsers 
      role="manager"
      title="Managers Management"
      description="Manage property managers who oversee properties and tenants."
    />
  )
}

export default ManagersManagement