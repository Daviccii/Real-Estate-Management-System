import React from 'react'
import './PropertyFilters.css'
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

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  vacant: 'Vacant',
  under_maintenance: 'Under maintenance',
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
  const typeLabel = PROPERTY_TYPES.find(t => t.value === typeFilter)?.label
  const budgetLabel = BUDGETS.find(b => b.value === budgetFilter)?.label
  const bedroomsLabel = BEDROOMS.find(b => b.value === bedroomsFilter)?.label

  const chips: { key: string; label: string; onRemove: () => void }[] = []
  if (typeFilter && typeLabel) chips.push({ key: 'type', label: typeLabel, onRemove: () => onTypeChange('') })
  if (cityFilter) chips.push({ key: 'city', label: cityFilter, onRemove: () => onCityChange('') })
  if (showBudgetFilter && budgetFilter && budgetLabel) chips.push({ key: 'budget', label: budgetLabel, onRemove: () => onBudgetChange('') })
  if (showBedroomsFilter && bedroomsFilter && bedroomsLabel) chips.push({ key: 'bedrooms', label: `${bedroomsLabel} bed${bedroomsFilter && bedroomsFilter !== '0' ? 's' : ''}`, onRemove: () => onBedroomsChange('') })
  if (statusFilter) chips.push({ key: 'status', label: STATUS_LABELS[statusFilter] || statusFilter, onRemove: () => onStatusChange('') })

  return (
    <div className="pn-filters-bar">
      <div className="pn-filters-row">
        {showPurposeFilter && (
          <label className="pn-filter-field">
            <span>Purpose</span>
            <select value={purposeFilter} onChange={e => onPurposeChange(e.target.value as PropertyPurpose | '')}>
              <option value="">All purposes</option>
              <option value="buy">Buy</option>
              <option value="rent">Rent</option>
              <option value="invest">Invest</option>
            </select>
          </label>
        )}

        <label className="pn-filter-field">
          <span>Property type</span>
          <select value={typeFilter} onChange={e=>onTypeChange(e.target.value)}>
            {PROPERTY_TYPES.map(t=> <option key={t.label} value={t.value}>{t.label}</option>)}
          </select>
        </label>

        <label className="pn-filter-field">
          <span>Location</span>
          <input
            list="city-suggestions"
            placeholder="Any location"
            value={cityFilter}
            onChange={e=>onCityChange(e.target.value)}
          />
          <datalist id="city-suggestions">
            {CITY_SUGGESTIONS.map(c => <option key={c} value={c} />)}
          </datalist>
        </label>

        {showBudgetFilter && (
          <label className="pn-filter-field">
            <span>Budget</span>
            <select value={budgetFilter} onChange={e=>onBudgetChange(e.target.value)}>
              {BUDGETS.map(b=> <option key={b.label} value={b.value}>{b.label}</option>)}
            </select>
          </label>
        )}

        {showBedroomsFilter && (
          <label className="pn-filter-field">
            <span>Bedrooms</span>
            <select value={bedroomsFilter} onChange={e=>onBedroomsChange(e.target.value)}>
              {BEDROOMS.map(b=> <option key={b.label} value={b.value}>{b.label} bed{b.value && b.value !== '0' ? 's' : ''}</option>)}
            </select>
          </label>
        )}

        <label className="pn-filter-field">
          <span>Status</span>
          <select value={statusFilter} onChange={e=>onStatusChange(e.target.value)}>
            <option value="">Any status</option>
            <option value="active">Active</option>
            <option value="vacant">Vacant</option>
            <option value="under_maintenance">Under maintenance</option>
          </select>
        </label>

        <label className="pn-filter-field">
          <span>Sort by</span>
          <select value={sort} onChange={e=>onSortChange(e.target.value)}>
            <option value="">Default</option>
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="units_desc">Most units</option>
            <option value="units_asc">Fewest units</option>
          </select>
        </label>

        <div className="pn-filters-actions">
          <button className="pn-btn pn-btn-primary" onClick={onApply}>Apply</button>
          {activeFilterCount > 0 && <button className="pn-btn pn-btn-ghost" onClick={onClear}>Clear all</button>}
        </div>
      </div>

      {chips.length > 0 && (
        <div className="pn-filters-chips">
          {chips.map(chip => (
            <span key={chip.key} className="pn-filter-chip">
              {chip.label}
              <button type="button" onClick={chip.onRemove} aria-label={`Remove ${chip.label} filter`}>×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default PropertyFilters