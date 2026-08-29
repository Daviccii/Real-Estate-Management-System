import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { Property } from '../types'
import { propertyService } from '../services/property'
import PropertyCard from '../components/PropertyCard'
import PropertyForm from '../components/PropertyForm'
import PropertyGrid from '../components/PropertyGrid'
import PropertyFilters from '../components/PropertyFilters'
import Pagination from '../components/Pagination'
import { useToast } from '../components/ToastProvider'
import { PROPERTY_TYPES, BUDGETS, BEDROOMS, CITY_SUGGESTIONS, budgetBucketBounds, extractPriceValue } from '../data/propertySearchOptions'
import { PropertyPurpose } from '../data/publicHomeContent'

const PAGE_SIZE = 9

const PURPOSES: { label: string; value: PropertyPurpose | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Buy', value: 'buy' },
  { label: 'Rent', value: 'rent' },
  { label: 'Invest', value: 'invest' },
]

// Note: Purpose buttons are kept for Explore page flexibility, but users are encouraged to use dedicated routes

const PropertiesPage: React.FC = () => {
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string | null>(null)
  const [items,setItems]=useState<Property[] | null>(null)
  const [showForm,setShowForm]=useState(false)
  const [page,setPage]=useState(1)
  const [hasMore,setHasMore]=useState(false)
  const [q,setQ]=useState('')
  const [typeFilter,setTypeFilter]=useState('')
  const [cityFilter,setCityFilter]=useState('')
  const [statusFilter,setStatusFilter]=useState('')
  const [sort,setSort]=useState('')
  const [purposeFilter,setPurposeFilter]=useState<PropertyPurpose | ''>('')
  const [budgetFilter,setBudgetFilter]=useState('')
  const [bedroomsFilter,setBedroomsFilter]=useState('')
  const [matched,setMatched]=useState(false)

  const { addToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const fetch = async (overrides?: { q?: string; type?: string; city?: string; status?: string; sort?: string; purpose?: string; page?: number }) => {
    setLoading(true); setError(null)
    const targetPage = overrides?.page ?? page
    try{
      const res = await propertyService.pagedList(targetPage, PAGE_SIZE, {
        search: (overrides?.q ?? q) || undefined,
        property_type: (overrides?.type ?? typeFilter) || undefined,
        city: (overrides?.city ?? cityFilter) || undefined,
        status: (overrides?.status ?? statusFilter) || undefined,
        sort: (overrides?.sort ?? sort) || undefined,
        purpose: (overrides?.purpose ?? purposeFilter) || undefined,
      })
      setItems(res)
      setHasMore(res.length === PAGE_SIZE)
      setPage(targetPage)
    }catch(e:any){ setError(String(e)) }
    setLoading(false)
  }

  // Seed every filter from the URL once on load — this is what makes the
  // homepage's Buy/Rent/Invest links, the hero search, and the match panel
  // actually land somewhere meaningful instead of an unfiltered page.
  useEffect(()=>{
    const params = new URLSearchParams(location.search)
    const urlType = params.get('property_type') || ''
    const urlCity = params.get('location') || params.get('city') || ''
    const urlStatus = params.get('status') || ''
    const urlSort = params.get('sort') || ''
    const urlQ = params.get('q') || ''
    const urlPurpose = (params.get('purpose') as PropertyPurpose | null) || ''
    const urlBudget = params.get('budget') || ''
    const urlBedrooms = params.get('bedrooms') || ''
    const urlMatch = params.get('match') === 'true'

    setTypeFilter(urlType)
    setCityFilter(urlCity)
    setStatusFilter(urlStatus)
    setSort(urlSort)
    setQ(urlQ)
    setPurposeFilter(urlPurpose)
    setBudgetFilter(urlBudget)
    setBedroomsFilter(urlBedrooms)
    setMatched(urlMatch)

    fetch({ q: urlQ, type: urlType, city: urlCity, status: urlStatus, sort: urlSort, purpose: urlPurpose, page: 1 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function syncUrl(next: Partial<{ q: string; type: string; city: string; status: string; sort: string; purpose: PropertyPurpose | ''; budget: string; bedrooms: string }>) {
    const state = {
      q, type: typeFilter, city: cityFilter, status: statusFilter, sort,
      purpose: purposeFilter, budget: budgetFilter, bedrooms: bedroomsFilter,
      ...next,
    }
    const params = new URLSearchParams()
    if (state.q) params.set('q', state.q)
    if (state.type) params.set('property_type', state.type)
    if (state.city) params.set('location', state.city)
    if (state.status) params.set('status', state.status)
    if (state.sort) params.set('sort', state.sort)
    if (state.purpose) params.set('purpose', state.purpose)
    if (state.budget) params.set('budget', state.budget)
    if (state.bedrooms) params.set('bedrooms', state.bedrooms)
    
    // For Explore page, we stay on /properties with purpose as query param
    navigate({ pathname: '/properties', search: params.toString() }, { replace: true })
  }

  function handleSearch() {
    syncUrl({})
    fetch({ page: 1 })
  }

  function handleClear() {
    setQ(''); setTypeFilter(''); setCityFilter(''); setStatusFilter(''); setSort('')
    setPurposeFilter(''); setBudgetFilter(''); setBedroomsFilter(''); setMatched(false)
    navigate('/properties', { replace: true })
    fetch({ q: '', type: '', city: '', status: '', sort: '', page: 1 })
  }

  function handlePrevPage() {
    if (page <= 1) return
    fetch({ page: page - 1 })
  }

  function handleNextPage() {
    if (!hasMore) return
    fetch({ page: page + 1 })
  }

  const handleCreate = async (payload:any)=>{
    setLoading(true)
    try{
      const created = await propertyService.create(payload)
      if(created){
        addToast({ message: 'Property created', type: 'success' })
        setShowForm(false)
        await fetch({ page: 1 })
      } else {
        addToast({ message: 'Failed to create property', type: 'error' })
      }
    }catch(err:any){
      addToast({ message: err?.message || 'Failed to create property', type: 'error' })
    }finally{ setLoading(false) }
  }

  // Budget and bedrooms are applied client-side as "soft" filters since they may
  // not be fully modeled on the backend yet. A listing missing that field stays
  // visible rather than being wrongly hidden just because the data isn't tracked.
  const filtered = useMemo(() => {
    const source = items || []
    return source.filter((p) => {
      if (bedroomsFilter && typeof p.bedrooms === 'number') {
        if (bedroomsFilter === '4-plus' ? p.bedrooms < 4 : p.bedrooms !== Number(bedroomsFilter)) return false
      }
      if (budgetFilter) {
        const bounds = budgetBucketBounds(budgetFilter)
        const value = extractPriceValue(p.price, p.price_label)
        if (bounds && value !== null && (value < bounds.min || value >= bounds.max)) return false
      }
      return true
    })
  }, [items, bedroomsFilter, budgetFilter])

  const activeFilterCount = [typeFilter, cityFilter, statusFilter, budgetFilter, bedroomsFilter].filter(Boolean).length

  // Dynamic header based on purpose (Explore shows generic content)
  const getHeaderTitle = () => {
    return 'Explore Properties'
  }

  const getHeaderSubtitle = () => {
    return 'Search properties by location, type, and more'
  }

  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:12}}>
        <div>
          <h2>{getHeaderTitle()}</h2>
          <p style={{color:'var(--text-secondary)',margin:0}}>{getHeaderSubtitle()}</p>
        </div>
        <div style={{display:'flex',gap:8,flexWrap:'wrap'}}>
          <input className="input" style={{flex:'1 1 220px',minWidth:0}} placeholder="Search by name, location or type" value={q} onChange={e=>setQ(e.target.value)} />
          <button className="button" style={{flexShrink:0}} onClick={handleSearch}>Search</button>
          <button className="button" style={{flexShrink:0}} onClick={()=>setShowForm(true)}>Add Property</button>
        </div>
      </div>

      <div style={{display:'flex',gap:8,marginBottom:12,flexWrap:'wrap'}}>
        {PURPOSES.map(p => (
          <button
            key={p.label}
            className={purposeFilter === p.value ? 'button' : 'button muted'}
            onClick={() => { setPurposeFilter(p.value); syncUrl({ purpose: p.value }); fetch({ purpose: p.value, page: 1 }) }}
          >
            {p.label}
          </button>
        ))}
      </div>
      <div style={{fontSize:'0.85em',color:'var(--text-secondary)',marginBottom:12}}>
        💡 For dedicated experiences, use <Link to="/buy" style={{color:'var(--primary)'}}>Buy</Link>, <Link to="/rent" style={{color:'var(--primary)'}}>Rent</Link>, or <Link to="/invest" style={{color:'var(--primary)'}}>Invest</Link> pages.
      </div>

      {matched && (
        <div style={{marginBottom:12,padding:'10px 14px',borderRadius:10,background:'rgba(31,95,191,0.08)',color:'#114b99'}}>
          Showing results based on what you told us on the homepage.
        </div>
      )}

      <PropertyFilters
        typeFilter={typeFilter}
        cityFilter={cityFilter}
        statusFilter={statusFilter}
        budgetFilter={budgetFilter}
        bedroomsFilter={bedroomsFilter}
        sort={sort}
        purposeFilter={purposeFilter}
        onTypeChange={setTypeFilter}
        onCityChange={setCityFilter}
        onStatusChange={setStatusFilter}
        onBudgetChange={setBudgetFilter}
        onBedroomsChange={setBedroomsFilter}
        onSortChange={setSort}
        onPurposeChange={setPurposeFilter}
        onApply={handleSearch}
        onClear={handleClear}
        activeFilterCount={activeFilterCount}
        showPurposeFilter={false}
        showBudgetFilter={true}
        showBedroomsFilter={true}
      />

      {showForm && <PropertyForm onSubmit={handleCreate} onCancel={()=>setShowForm(false)} />}

      <PropertyGrid 
        properties={filtered}
        loading={loading}
        error={error}
        emptyMessage={activeFilterCount > 0 ? 'No properties match these filters. Try widening your search.' : 'No properties found. Try a different search.'}
      />

      <Pagination page={page} hasMore={hasMore} onPrev={handlePrevPage} onNext={handleNextPage} loading={loading} />
    </div>
  )
}

export default PropertiesPage