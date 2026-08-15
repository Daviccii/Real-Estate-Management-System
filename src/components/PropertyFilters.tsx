import React from 'react'
import { PropertyPurpose } from '../data/publicHomeContent'
import { PROPERTY_TYPES, BUDGETS, BEDROOMS, CITY_SUGGESTIONS } from '../data/propertySearchOptions'

interface PropertyFiltersProps {
  typeFilter: string
  cityFilter: string
  statusFilter: string
  budgetFilter: string
  bedroomsFilter: string
  sort: string
  purposeFilter: PropertyPurpose | ''
  onTypeChange: (value: string) => void
  onCityChange: (value: string) => void
  onStatusChange: (value: string) => void
  onBudgetChange: (value: string) => void
  onBedroomsChange: (value: string) => void
  onSortChange: (value: string) => void
  onPurposeChange: (value: PropertyPurpose | '') => void
  onApply: () => void
  onClear: () => void
  activeFilterCount: number
  showPurposeFilter?: boolean
  showBudgetFilter?: boolean
  showBedroomsFilter?: boolean
}

const PropertyFilters: React.FC<PropertyFiltersProps> = ({
  typeFilter,
  cityFilter,
  statusFilter,
  budgetFilter,
  bedroomsFilter,
  sort,
  purposeFilter,
  onTypeChange,
  onCityChange,
  onStatusChange,
  onBudgetChange,
  onBedroomsChange,
  onSortChange,
  onPurposeChange,
  onApply,
  onClear,
  activeFilterCount,
  showPurposeFilter = true,
  showBudgetFilter = true,
  showBedroomsFilter = true,
}) => {
  return (
    <div style={{display:'flex',gap:8,marginBottom:12,alignItems:'center',flexWrap:'wrap'}}>
      {showPurposeFilter && (
        <select 
          className="input" 
          value={purposeFilter} 
          onChange={e => onPurposeChange(e.target.value as PropertyPurpose | '')}
        >
          <option value="">All purposes</option>
          <option value="buy">Buy</option>
          <option value="rent">Rent</option>
          <option value="invest">Invest</option>
        </select>
      )}
      
      <select className="input" value={typeFilter} onChange={e=>onTypeChange(e.target.value)}>
        {PROPERTY_TYPES.map(t=> <option key={t.label} value={t.value}>{t.label}</option>)}
      </select>
      
      <input
        className="input"
        list="city-suggestions"
        placeholder="Any location"
        value={cityFilter}
        onChange={e=>onCityChange(e.target.value)}
      />
      <datalist id="city-suggestions">
        {CITY_SUGGESTIONS.map(c => <option key={c} value={c} />)}
      </datalist>
      
      {showBudgetFilter && (
        <select className="input" value={budgetFilter} onChange={e=>onBudgetChange(e.target.value)}>
          {BUDGETS.map(b=> <option key={b.label} value={b.value}>{b.label}</option>)}
        </select>
      )}
      
      {showBedroomsFilter && (
        <select className="input" value={bedroomsFilter} onChange={e=>onBedroomsChange(e.target.value)}>
          {BEDROOMS.map(b=> <option key={b.label} value={b.value}>{b.label} bed{b.value && b.value !== '0' ? 's' : ''}</option>)}
        </select>
      )}
      
      <select className="input" value={statusFilter} onChange={e=>onStatusChange(e.target.value)}>
        <option value="">Any status</option>
        <option value="active">Active</option>
        <option value="vacant">Vacant</option>
        <option value="under_maintenance">Under maintenance</option>
      </select>
      
      <select className="input" value={sort} onChange={e=>onSortChange(e.target.value)}>
        <option value="">Sort</option>
        <option value="newest">Newest</option>
        <option value="oldest">Oldest</option>
        <option value="units_desc">Most units</option>
        <option value="units_asc">Fewest units</option>
      </select>
      
      <button className="button" onClick={onApply}>Apply</button>
      {activeFilterCount > 0 && <button className="button muted" onClick={onClear}>Clear ({activeFilterCount})</button>}
    </div>
  )
}

export default PropertyFilters