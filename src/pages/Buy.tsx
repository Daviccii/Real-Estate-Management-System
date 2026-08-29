import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Property } from '../types'
import { propertyService } from '../services/property'
import PropertyGrid from '../components/PropertyGrid'
import PropertyFilters from '../components/PropertyFilters'
import Pagination from '../components/Pagination'
import { useToast } from '../components/ToastProvider'
import { PROPERTY_TYPES, BUDGETS, BEDROOMS, CITY_SUGGESTIONS, budgetBucketBounds, extractPriceValue } from '../data/propertySearchOptions'

const PAGE_SIZE = 9

const BuyPage: React.FC = () => {
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState<string | null>(null)
  const [items,setItems]=useState<Property[] | null>(null)
  const [page,setPage]=useState(1)
  const [hasMore,setHasMore]=useState(false)
  const [q,setQ]=useState('')
  const [typeFilter,setTypeFilter]=useState('')
  const [cityFilter,setCityFilter]=useState('')
  const [statusFilter,setStatusFilter]=useState('')
  const [sort,setSort]=useState('')
  const [budgetFilter,setBudgetFilter]=useState('')
  const [bedroomsFilter,setBedroomsFilter]=useState('')
  const [matched,setMatched]=useState(false)

  const { addToast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const fetch = async (overrides?: { q?: string; type?: string; city?: string; status?: string; sort?: string; page?: number }) => {
    setLoading(true); setError(null)
    const targetPage = overrides?.page ?? page
    try{
      const res = await propertyService.pagedList(targetPage, PAGE_SIZE, {
        search: (overrides?.q ?? q) || undefined,
        property_type: (overrides?.type ?? typeFilter) || undefined,
        city: (overrides?.city ?? cityFilter) || undefined,
        status: (overrides?.status ?? statusFilter) || undefined,
        sort: (overrides?.sort ?? sort) || undefined,
        purpose: 'buy',
      })
      setItems(res)
      // No filtered total-count endpoint exists, so "is there a next page" is
      // inferred from whether this page came back full. Budget/bedroom
      // filters below are applied client-side on top of this page's results,
      // so a page may display fewer than PAGE_SIZE cards even when hasMore
      // is true — the next page is still fetched from the server correctly.
      setHasMore(res.length === PAGE_SIZE)
      setPage(targetPage)
    }catch(e:any){ setError(String(e)) }
    setLoading(false)
  }

  // Seed filters from URL on load
  useEffect(()=>{
    const params = new URLSearchParams(location.search)
    const urlType = params.get('property_type') || ''
    const urlCity = params.get('location') || params.get('city') || ''
    const urlStatus = params.get('status') || ''
    const urlSort = params.get('sort') || ''
    const urlQ = params.get('q') || ''
    const urlBudget = params.get('budget') || ''
    const urlBedrooms = params.get('bedrooms') || ''
    const urlMatch = params.get('match') === 'true'

    setTypeFilter(urlType)
    setCityFilter(urlCity)
    setStatusFilter(urlStatus)
    setSort(urlSort)
    setQ(urlQ)
    setBudgetFilter(urlBudget)
    setBedroomsFilter(urlBedrooms)
    setMatched(urlMatch)

    fetch({ q: urlQ, type: urlType, city: urlCity, status: urlStatus, sort: urlSort, page: 1 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function syncUrl(next: Partial<{ q: string; type: string; city: string; status: string; sort: string; budget: string; bedrooms: string }>) {
    const state = {
      q, type: typeFilter, city: cityFilter, status: statusFilter, sort,
      budget: budgetFilter, bedrooms: bedroomsFilter,
      ...next,
    }
    const params = new URLSearchParams()
    if (state.q) params.set('q', state.q)
    if (state.type) params.set('property_type', state.type)
    if (state.city) params.set('location', state.city)
    if (state.status) params.set('status', state.status)
    if (state.sort) params.set('sort', state.sort)
    if (state.budget) params.set('budget', state.budget)
    if (state.bedrooms) params.set('bedrooms', state.bedrooms)
    navigate({ pathname: '/buy', search: params.toString() }, { replace: true })
  }

  function handleSearch() {
    syncUrl({})
    fetch({ page: 1 })
  }

  function handleClear() {
    setQ(''); setTypeFilter(''); setCityFilter(''); setStatusFilter(''); setSort('')
    setBudgetFilter(''); setBedroomsFilter(''); setMatched(false)
    navigate('/buy', { replace: true })
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

  // Budget and bedrooms are applied client-side as "soft" filters
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

  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:12,marginBottom:12}}>
        <div>
          <h2>Find a Property to Buy</h2>
          <p style={{color:'var(--text-secondary)',margin:0}}>Discover properties available for purchase</p>
        </div>
        <div style={{display:'flex',gap:8,flex:'1 1 320px',maxWidth:420}}>
          <input className="input" style={{flex:1,minWidth:0}} placeholder="Search by name, location or type" value={q} onChange={e=>setQ(e.target.value)} />
          <button className="button" style={{flexShrink:0}} onClick={handleSearch}>Search</button>
        </div>
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
        purposeFilter="buy"
        onTypeChange={setTypeFilter}
        onCityChange={setCityFilter}
        onStatusChange={setStatusFilter}
        onBudgetChange={setBudgetFilter}
        onBedroomsChange={setBedroomsFilter}
        onSortChange={setSort}
        onPurposeChange={() => {}}
        onApply={handleSearch}
        onClear={handleClear}
        activeFilterCount={activeFilterCount}
        showPurposeFilter={false}
        showBudgetFilter={true}
        showBedroomsFilter={true}
      />

      <PropertyGrid 
        properties={filtered}
        loading={loading}
        error={error}
        emptyMessage={activeFilterCount > 0 ? 'No properties match these filters. Try widening your search.' : 'No properties available for purchase. Try a different search.'}
      />

      <Pagination page={page} hasMore={hasMore} onPrev={handlePrevPage} onNext={handleNextPage} loading={loading} />
    </div>
  )
}

export default BuyPage