import RoleUsers from './RoleUsers'

const TenantsManagement: React.FC = () => {
  return (
    <RoleUsers 
      role="tenant"
      title="Tenants Management"
      description="Manage tenants who rent or lease properties."
    />
  )
}

export default TenantsManagement