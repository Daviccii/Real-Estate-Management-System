import sys
import os
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.database.database import SessionLocal
from app.utils.time import utc_now
from app.models.user import User
from app.models.property import Property
from app.models.unit import Unit
from app.models.lease import Lease
from app.models.payment import Payment
from app.models.maintenance import Maintenance
from app.models.inquiry import Inquiry
from app.models.lead import Lead
from app.models.viewing import Viewing
from app.models.building import Building
from app.models.application import RentalApplication
from app.models.verification import VerificationRecord
from app.models.verification_evidence import VerificationEvidence
from app.models.property_media import PropertyMedia
from app.models.owner_expense import OwnerExpense
from app.models.provider_invoice import ProviderInvoice
from app.models.provider_rating import ProviderRating
from app.models.service_marketplace import ServiceProviderProfile, MaintenanceWorkOrder
from app.models.role_profiles import TenantProfile, OwnerProfile, AgentProfile, ManagerProfile
from app.utils.security import get_password_hash

def seed_all():
    db = SessionLocal()
    try:
        print("--- Seeding Roles, Users, and Ecosystem Data ---")
        
        # 1. Admin Account (Gabriel)
        admin = db.query(User).filter(User.email == 'kebirogabriel@gmail.com').first()
        if not admin:
            admin = User(
                email='kebirogabriel@gmail.com',
                hashed_password=get_password_hash('onsomuRiley2022'),
                full_name='Gabriel Onsomu',
                role='admin',
                roles_csv='admin,manager,owner,agent,tenant,service_provider',
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        else:
            admin.roles_csv = 'admin,manager,owner,agent,tenant,service_provider'
            admin.is_active = True
            admin.is_verified = True
            db.add(admin)
            db.commit()

        # 2. Manager Account
        manager_email = 'manager@realestate.com'
        manager = db.query(User).filter(User.email == manager_email).first()
        if not manager:
            manager = User(
                email=manager_email,
                hashed_password=get_password_hash('Manager123!'),
                full_name='Sarah Mwangi',
                phone='+254712345678',
                role='manager',
                roles_csv='manager',
                is_active=True,
                is_verified=True
            )
            db.add(manager)
            db.commit()
            db.refresh(manager)
        
        mgr_profile = db.query(ManagerProfile).filter(ManagerProfile.user_id == manager.id).first()
        if not mgr_profile:
            mgr_profile = ManagerProfile(
                user_id=manager.id,
                company_name='Apex Property Management Ltd',
                license_number='RPM-2024-889',
                operating_areas='Westlands, Kilimani, Lavington',
                max_managed_units=150,
                emergency_phone='+254712345678',
                is_verified=True
            )
            db.add(mgr_profile)
            db.commit()

        # 3. Owner Account
        owner_email = 'owner@realestate.com'
        owner = db.query(User).filter(User.email == owner_email).first()
        if not owner:
            owner = User(
                email=owner_email,
                hashed_password=get_password_hash('Owner123!'),
                full_name='David Kamau',
                phone='+254722112233',
                role='owner',
                roles_csv='owner',
                is_active=True,
                is_verified=True
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

        own_profile = db.query(OwnerProfile).filter(OwnerProfile.user_id == owner.id).first()
        if not own_profile:
            own_profile = OwnerProfile(
                user_id=owner.id,
                owner_type='individual',
                company_name='Kamau Holdings',
                tax_pin='A009876543Z',
                national_id_number='28492011',
                payout_phone='+254722112233',
                bank_name='Standard Chartered',
                bank_account_number='0100234567800',
                bank_account_name='David Kamau',
                emergency_contact='Jane Kamau (+254722998877)',
                is_verified=True
            )
            db.add(own_profile)
            db.commit()

        # 4. Agent Account
        agent_email = 'agent@realestate.com'
        agent = db.query(User).filter(User.email == agent_email).first()
        if not agent:
            agent = User(
                email=agent_email,
                hashed_password=get_password_hash('Agent123!'),
                full_name='Grace Wanjiku',
                phone='+254733445566',
                role='agent',
                roles_csv='agent',
                is_active=True,
                is_verified=True
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)

        agt_profile = db.query(AgentProfile).filter(AgentProfile.user_id == agent.id).first()
        if not agt_profile:
            agt_profile = AgentProfile(
                user_id=agent.id,
                agency_name='Prime Properties Real Estate',
                license_number='EARB-7432',
                operating_areas='Nairobi CBD, Kilimani, Westlands, Karen',
                specialties='Luxury Residential, Commercial Leasing',
                years_experience=6,
                bio='Top-rated realtor specializing in residential investments and prime rentals.',
                commission_rate=5.0,
                is_verified=True
            )
            db.add(agt_profile)
            db.commit()

        # 5. Tenant Account
        tenant_email = 'tenant@realestate.com'
        tenant = db.query(User).filter(User.email == tenant_email).first()
        if not tenant:
            tenant = User(
                email=tenant_email,
                hashed_password=get_password_hash('Tenant123!'),
                full_name='Brian Ochieng',
                phone='+254744556677',
                role='tenant',
                roles_csv='tenant',
                is_active=True,
                is_verified=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        ten_profile = db.query(TenantProfile).filter(TenantProfile.user_id == tenant.id).first()
        if not ten_profile:
            ten_profile = TenantProfile(
                user_id=tenant.id,
                preferred_locations='Westlands, Kilimani',
                min_budget=60000,
                max_budget=120000,
                preferred_bedrooms=2,
                preferred_property_type='apartment',
                desired_move_in_date='2026-11-01',
                household_size=2,
                has_pets='no',
                employment_status='employed',
                monthly_income='KES 250,000',
                employer_name='Safaricom PLC',
                job_title='Senior Software Engineer',
                emergency_contact_name='Faith Ochieng',
                emergency_contact_phone='+254744001122'
            )
            db.add(ten_profile)
            db.commit()

        # 6. Service Provider Account
        provider_email = 'provider@realestate.com'
        provider = db.query(User).filter(User.email == provider_email).first()
        if not provider:
            provider = User(
                email=provider_email,
                hashed_password=get_password_hash('Provider123!'),
                full_name='Kelvin Kiprono',
                phone='+254755667788',
                role='service_provider',
                roles_csv='service_provider',
                is_active=True,
                is_verified=True
            )
            db.add(provider)
            db.commit()
            db.refresh(provider)

        prv_profile = db.query(ServiceProviderProfile).filter(ServiceProviderProfile.user_id == provider.id).first()
        if not prv_profile:
            prv_profile = ServiceProviderProfile(
                user_id=provider.id,
                business_name='ProFix Plumbing & Electrical Works',
                specialty='Plumbing, HVAC, Electrical',
                license_number='EPRA-ELEC-442',
                hourly_rate='KES 2,500/hr',
                years_experience=8,
                rating=4.9,
                bio='Licensed technician offering emergency plumbing and certified electrical maintenance.',
                service_areas='Nairobi Metro, Kiambu',
                is_verified=True
            )
            db.add(prv_profile)
            db.commit()

        # 7. Assign properties to Owner, Manager, Agent
        properties = db.query(Property).all()
        for idx, prop in enumerate(properties):
            prop.owner_id = owner.id
            prop.manager_id = manager.id
            prop.agent_id = agent.id
            prop.is_verified = True
            prop.verification_status = "verified"
            prop.listing_status = prop.listing_status or "active"
            prop.is_demo = True
            prop.allow_direct_contact = True
            db.add(prop)
        db.commit()

        # 8. Add a managed building record so the presentation includes a
        # portfolio-level asset, not only standalone listings.
        first_property = properties[0] if properties else None
        building_names = ["Apex Heights Residences", "Kilimani Garden Court", "Westlands Business Square"]
        for index, property_obj in enumerate(properties[:3]):
            if not db.query(Building).filter(Building.property_id == property_obj.id).first():
                building = Building(
                    property_id=property_obj.id,
                    name=building_names[index],
                    building_type="mixed_use" if index == 2 else "residential",
                    address=property_obj.address or "Nairobi Central",
                    city=property_obj.city or "Nairobi",
                    county=property_obj.county or "Nairobi",
                    sub_location=property_obj.sub_location or "Westlands",
                    total_floors=8 + index,
                    units_count=32 + index * 12,
                    amenities="CCTV, lift, backup generator, borehole, parking",
                    year_built=2020 + index,
                    description="Managed asset in the PropNoxa presentation dataset.",
                )
                db.add(building)
                db.flush()
                property_obj.building_id = building.id
        db.commit()

        # 9. Structured media and verification evidence for presentation listings.
        for prop in properties[:8]:
            if not db.query(PropertyMedia).filter(PropertyMedia.property_id == prop.id).first():
                image_url = prop.image_url or "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=80&w=1200&auto=format&fit=crop"
                db.add(PropertyMedia(
                    property_id=prop.id,
                    url=image_url,
                    media_type="image",
                    source_type="CONTROLLED_DEMO",
                    source_name="PropNoxa Board Demo Dataset",
                    license_reference="Internal presentation dataset; not an external ownership claim.",
                    caption=f"Primary presentation image for {prop.name}",
                    is_primary=True,
                    is_public=True,
                ))
            verification = db.query(VerificationRecord).filter(
                VerificationRecord.entity_type == "property",
                VerificationRecord.entity_id == prop.id,
            ).first()
            if not verification:
                verification = VerificationRecord(
                    entity_type="property",
                    entity_id=prop.id,
                    status="verified",
                    verification_type="controlled_demo_review",
                    submitted_data_json='{"source":"PropNoxa Board Demo Dataset","scope":"presentation"}',
                    reviewed_by_id=admin.id,
                    review_notes="Controlled demo listing reviewed for presentation use.",
                    reviewed_at=utc_now(),
                )
                db.add(verification)
                db.flush()
                db.add(VerificationEvidence(
                    verification_id=verification.id,
                    evidence_type="dataset_record",
                    reference="PROP_NOXA_DEMO",
                    description="Internal provenance marker for controlled presentation data.",
                    created_by_id=admin.id,
                ))
        db.commit()

        # 9. Ensure Units exist
        first_prop = properties[0] if properties else None
        if first_prop:
            units = db.query(Unit).filter(Unit.property_id == first_prop.id).all()
            if not units:
                unit1 = Unit(
                    property_id=first_prop.id,
                    unit_number='A-102',
                    unit_type='2-Bedroom',
                    rent='KES 85,000',
                    status='occupied',
                    bedrooms=2,
                    bathrooms=2,
                    area='1,200 sqft'
                )
                unit2 = Unit(
                    property_id=first_prop.id,
                    unit_number='B-204',
                    unit_type='3-Bedroom',
                    rent='KES 110,000',
                    status='available',
                    bedrooms=3,
                    bathrooms=2,
                    area='1,600 sqft'
                )
                db.add(unit1)
                db.add(unit2)
                db.commit()
                db.refresh(unit1)
            else:
                unit1 = units[0]

            # 10. Active Lease for Tenant
            existing_lease = db.query(Lease).filter(Lease.tenant_id == tenant.id).first()
            if not existing_lease:
                lease = Lease(
                    tenant_id=tenant.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    start_date=utc_now() - timedelta(days=60),
                    end_date=utc_now() + timedelta(days=305),
                    rent_amount='85000',
                    deposit='85000',
                    payment_due_date=5,
                    status='active',
                    notes='Standard 12-month residential tenancy agreement.'
                )
                db.add(lease)
                db.commit()
                db.refresh(lease)

                # 11. Payments for the Lease
                p1 = Payment(
                    tenant_id=tenant.id,
                    lease_id=lease.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    amount='85000',
                    due_date=utc_now() + timedelta(days=4),
                    payment_type='rent',
                    status='pending',
                    payment_method='mpesa',
                    reference='MPESA-PEND-1002'
                )
                p2 = Payment(
                    tenant_id=tenant.id,
                    lease_id=lease.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    amount='85000',
                    due_date=utc_now() - timedelta(days=26),
                    payment_date=utc_now() - timedelta(days=25),
                    payment_type='rent',
                    status='completed',
                    payment_method='mpesa',
                    reference='QWE871629Z'
                )
                db.add(p1)
                db.add(p2)
                db.commit()

                # 12. Maintenance Ticket
                maint = Maintenance(
                    tenant_id=tenant.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    assigned_manager_id=manager.id,
                    title='Kitchen Sink Pipe Leakage',
                    description='Under-sink pipe has a steady drip causing dampness in cabinet.',
                    priority='medium',
                    status='in_progress',
                    category='plumbing'
                )
                db.add(maint)
                db.commit()
                db.refresh(maint)

                # 13. Work Order for Provider
                wo = MaintenanceWorkOrder(
                    maintenance_id=maint.id,
                    provider_id=provider.id,
                    status='in_progress',
                    total_cost=4500,
                    materials_cost=1500,
                    labor_cost=3000,
                    scheduled_date=utc_now() + timedelta(days=1),
                    completion_notes=None
                )
                db.add(wo)
                db.commit()

            # 14. Leads and Viewings for Agent
            existing_lead = db.query(Lead).filter(Lead.agent_id == agent.id).first()
            if not existing_lead:
                lead = Lead(
                    agent_id=agent.id,
                    prospect_name='Winnie Mutua',
                    prospect_email='winnie.mutua@example.com',
                    prospect_phone='+254701234567',
                    property_id=first_prop.id,
                    stage='viewing',
                    notes='Interested in 2-bedroom unit with parking.',
                    estimated_budget='90,000'
                )
                db.add(lead)
                db.commit()
                db.refresh(lead)

                viewing = Viewing(
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    prospect_id=tenant.id,
                    host_user_id=agent.id,
                    viewing_date='2026-10-05',
                    start_time='14:00',
                    end_time='15:00',
                    status='confirmed',
                    notes='Client requested on-site tour.'
                )
                db.add(viewing)
                db.commit()

            # Keep at least one realistic application visible in the manager queue.
            if not db.query(RentalApplication).filter(
                RentalApplication.applicant_id == tenant.id,
                RentalApplication.property_id == first_prop.id,
            ).first():
                db.add(RentalApplication(
                    applicant_id=tenant.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    status="under_review",
                    desired_move_in_date=utc_now() + timedelta(days=14),
                    monthly_income="240000",
                    employment_status="employed",
                    employer_name="Nairobi Digital Services",
                    job_title="Operations Lead",
                    occupants_count=2,
                    has_pets="no",
                    emergency_contact_name="Mary Njeri",
                    emergency_contact_phone="+254700000111",
                    documents_json='{"identity":"protected://demo/tenant-identity","income":"protected://demo/tenant-income"}',
                ))
                db.commit()

            # Seed a second application with a different review state.
            if not db.query(RentalApplication).filter(
                RentalApplication.applicant_id == owner.id,
                RentalApplication.property_id == first_prop.id,
            ).first():
                db.add(RentalApplication(
                    applicant_id=owner.id,
                    property_id=first_prop.id,
                    unit_id=unit1.id,
                    status="submitted",
                    desired_move_in_date=utc_now() + timedelta(days=30),
                    monthly_income="310000",
                    employment_status="self-employed",
                    employer_name="Kamau Holdings",
                    job_title="Director",
                    occupants_count=1,
                    has_pets="no",
                    documents_json='{"identity":"protected://demo/owner-identity"}',
                ))
                db.commit()

            # Multiple appointment states make the agent calendar presentation-ready.
            if db.query(Viewing).filter(Viewing.property_id == first_prop.id).count() < 3:
                for viewing_date, viewing_status, prospect_id in [
                    ("2026-10-08", "requested", owner.id),
                    ("2026-10-12", "completed", tenant.id),
                ]:
                    db.add(Viewing(
                        property_id=first_prop.id,
                        unit_id=unit1.id,
                        prospect_id=prospect_id,
                        host_user_id=agent.id,
                        viewing_date=viewing_date,
                        start_time="10:00",
                        end_time="11:00",
                        status=viewing_status,
                        notes="Presentation calendar appointment.",
                    ))
                db.commit()

            if not db.query(OwnerExpense).filter(OwnerExpense.owner_id == owner.id).first():
                db.add_all([
                    OwnerExpense(owner_id=owner.id, property_id=first_prop.id, category="repairs", amount="45000", description="Roof and gutter maintenance", status="paid"),
                    OwnerExpense(owner_id=owner.id, property_id=first_prop.id, category="management_fee", amount="12000", description="Monthly property management fee", status="recorded"),
                ])
                db.commit()

            maintenance_record = db.query(Maintenance).filter(Maintenance.property_id == first_prop.id).first()
            if maintenance_record and not db.query(ProviderInvoice).filter(ProviderInvoice.provider_id == provider.id).first():
                db.add(ProviderInvoice(
                    provider_id=provider.id,
                    maintenance_id=maintenance_record.id,
                    invoice_number="PNX-INV-2026-001",
                    amount="4500",
                    status="submitted",
                    description="Kitchen sink pipe repair and materials",
                    issued_at=utc_now() - timedelta(days=2),
                    due_at=utc_now() + timedelta(days=12),
                ))
                db.add(ProviderRating(
                    provider_id=provider.id,
                    reviewer_id=manager.id,
                    maintenance_id=maintenance_record.id,
                    score=5,
                    comment="Prompt attendance, clear quotation, and clean completion.",
                ))
                db.commit()

        print("--- All Roles and Ecosystem Data Seeded Successfully! ---")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    seed_all()
