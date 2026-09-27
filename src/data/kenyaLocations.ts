// Kenya's 47 counties (Constitution of Kenya, 2010) plus well-known
// neighbourhoods/areas for the major counties. Used by search filters and
// listing forms so locations are entered consistently and can be filtered on.
export const KENYA_COUNTIES: string[] = [
  'Mombasa', 'Kwale', 'Kilifi', 'Tana River', 'Lamu',
  'Taita Taveta', 'Garissa', 'Wajir', 'Mandera', 'Marsabit',
  'Isiolo', 'Meru', 'Tharaka Nithi', 'Embu', 'Kitui',
  'Machakos', 'Makueni', 'Nyandarua', 'Nyeri', 'Kirinyaga',
  'Murang\'a', 'Kiambu', 'Turkana', 'West Pokot', 'Samburu',
  'Trans Nzoia', 'Uasin Gishu', 'Elgeyo Marakwet', 'Nandi', 'Baringo',
  'Laikipia', 'Nakuru', 'Narok', 'Kajiado', 'Kericho',
  'Bomet', 'Kakamega', 'Vihiga', 'Bungoma', 'Busia',
  'Siaya', 'Kisumu', 'Homa Bay', 'Migori', 'Kisii',
  'Nyamira', 'Nairobi',
]

// Major towns/areas worth suggesting per county. Counties not listed simply
// fall back to the free-text location input.
export const COUNTY_AREAS: Record<string, string[]> = {
  Nairobi: [
    'Westlands', 'Kilimani', 'Karen', 'Lavington', 'Kileleshwa', 'Riverside',
    'Spring Valley', 'Runda', 'Muthaiga', 'Garden Estate', 'Parklands',
    'South C', 'South B', 'Langata', 'Ngong Road', 'Kasarani', 'Roysambu',
    'Embakasi', 'Donholm', 'Buruburu', 'Ngara', 'Kilimani',
  ],
  Mombasa: ['Nyali', 'Bamburi', 'Mtwapa', 'Shanzu', 'Tudor', 'Kizingo', 'Likoni', 'Diani'],
  Kiambu: ['Ruiru', 'Juja', 'Thika', 'Kikuyu', 'Limuru', 'Karen Hardy', 'Mwiki', 'Githurai 45', 'Ruaka', 'Kiambu Town'],
  Kajiado: ['Ngong', 'Kitengela', 'Ongata Rongai', 'Kiserian', 'Mlolongo', 'Namanga', 'Mashuuru'],
  Machakos: ['Machakos Town', 'Mlolongo', 'Athi River', 'Syokimau', 'Mavoko', 'Kangundo', 'Tala'],
  Nakuru: ['Nakuru CBD', 'Milimani', 'Section 58', 'Naka', 'Free Area', 'Naivasha', 'Njoro', 'Molo', 'Gilgil'],
  Kisumu: ['Milimani', 'Tom Mboya', 'Kondele', 'Nyalenda', 'Mamboleo', 'Riat Hills', 'Ahero'],
  'Uasin Gishu': ['Eldoret CBD', 'Kapsoya', 'Langas', 'Annex', 'Elgon View', 'Kesses', 'Turbo'],
  Kilifi: ['Malindi', 'Watamu', 'Kilifi Town', 'Mtwapa', 'Mariakani', 'Mazeras'],
  Nyeri: ['Kamakwa', 'Karatina', 'Mukurweini', 'Othaya', 'Nyeri CBD'],
  Kakamega: ['Kakamega Town', 'Lurambo', 'Milimani', 'Sheywe', 'Mumias', 'Webuye Road'],
}

// Flat list combining every county and every known area — used for datalist
// suggestions so a visitor can type either a county or a neighbourhood.
export const LOCATION_SUGGESTIONS: string[] = [
  ...KENYA_COUNTIES,
  ...Object.values(COUNTY_AREAS).flat(),
]
