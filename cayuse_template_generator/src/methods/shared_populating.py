from datetime import datetime
from methods.utils import strip_html, find_closest_match, format_string, extract_titles

ACTIVITY_ASSOCIATIONS = {
    'Research': 'Research on Campus',
    'Conference': 'General and Administrative Purpose on Campus',
    'Other': 'Other Institutional Activity',
    'Training': 'Instruction on Campus',
    'Course Development': 'Experimental Development Research on Campus Experimental',
    'Equipment': 'Equipment on Campus',
    'Other - Center Development': 'Other Sponsored Activity on Campus',
    'Program Development': 'Experimental Development Research on Campus Experimental',
    'Research/Training': 'Research Training on Campus',
    'Student Support': 'Fellowship'
}

def determine_grant_status(grant):
    project_status = str(grant['Status']).capitalize()
    if project_status:
        if project_status == "Funded":
            funded_threshold = datetime.strptime('2024-01-01', '%Y-%m-%d')
            project_end_date = grant['End_Date_Req'] or grant['End_Date'] or grant['Date_Submitted']
            if project_end_date:
                return ("Active" if project_end_date >= funded_threshold else "Closed")
            else:
                raise Exception("Funded grant is not assigned an 'End_Date_Req' value in the database which is crucial towards determining a status.")
        elif project_status == "Pending":
            pending_threshold =  datetime.strptime('2024-06-30', '%Y-%m-%d')
            project_start_date = grant['Start_Date_Req'] or grant['Date_Submitted'] or grant['Start_Date']
            if project_start_date:
                return ("Active" if project_start_date >= pending_threshold else "Closed")
            else:
                raise Exception("Pending grant is missing a 'Start_Date_Req' value in the database which is crucial towards determining a status.")
        elif project_status in ["Withdrawn","Unsubmitted","Rejected"]:
            return "Closed"
        else:
            raise Exception("Grant was assigned an invalid Status in the database.")
    else:
        raise Exception("Grant is missing a Status in the database.")
    
# Needs fixing
def determine_grant_discipline(instance, grant):
    valid_disciplines = instance.DISCIPLINES
    project_discipline = grant['Discipline'] or grant['Primary_Dept']   # 1600 -> 450
    if project_discipline:
        
        if project_discipline.isdigit():
            project_discipline = int(project_discipline)
            if project_discipline in valid_disciplines:
                return valid_disciplines[project_discipline]
            else:
                # print("Invalid discipline(Int): ", project_discipline)
                raise Exception("Grant does not have a valid Discipline ID in the database")
        else:
            if project_discipline in valid_disciplines.values():
                return project_discipline
            else:
                closest_match = find_closest_match(project_discipline, valid_disciplines.values())
                if closest_match:
                    # print("Closest discipline(String): ", project_discipline, closest_match)
                    return project_discipline
                else:
                    # print("Invalid discipline(String): ", project_discipline)
                    raise Exception("Grant does not have a valid Discipline in the database")
    else:
        raise Exception("Grant does not have a Discipline in the database")
    
# Needs fixing
def determine_grant_admin_unit(instance, grant):
    org_units = instance.ORG_UNITS
    org_centers = instance.ORG_CENTERS
    project_primary_dept = grant['Primary_Dept']
    
    if project_primary_dept:
        org_unit_keys = [str(item) for item in org_units.keys()]
        if project_primary_dept in org_unit_keys:
            return project_primary_dept, org_units[project_primary_dept]['Primary Code'], None
        else:
            closest_valid_dept = find_closest_match(project_primary_dept, org_unit_keys)
            if closest_valid_dept:
                return closest_valid_dept, org_units[closest_valid_dept]['Primary Code'], None
            else:
                org_center_keys = [str(item) for item in org_centers.keys()]
                if project_primary_dept in org_center_keys:
                    project_center = org_centers[project_primary_dept]
                    return project_center['Admin Unit'], project_center['Admin Unit Code'], project_primary_dept
                else:
                    closest_valid_center = find_closest_match(project_primary_dept, org_center_keys)
                    if closest_valid_center:
                        project_center = org_centers[closest_valid_center]
                        return project_center['Admin Unit'], project_center['Admin Unit Code'], closest_valid_center
                    else:
                        raise Exception(f"Failed to determine a valid department for {project_primary_dept}")
    else:
        raise Exception("Grant does not have a primary department in the database.")
    
def determine_instrument_type(self, grant):
    valid_types = self.INSTRUMENT_TYPES
    project_award_type = grant['Award Type']

    if project_award_type:
        type_letter, type_title = project_award_type.split('-')
        type_letter.strip()
        type_title.strip()

        for type_name, association in valid_types.items():
            if type_letter in association.keys():
                return type_name
            closest_valid_type = find_closest_match(type_title, [str(item) for item in association.values()], case_sensitive=False)
            if closest_valid_type:
                return type_name

    str_id = str(grant['Grant_ID'])
    if str_id.startswith('6'):
        return "PSC CUNY"
        

def determine_sponsor(instance, sponsor):
    if not sponsor:
        raise Exception("Grant does not have a sponsor assigned to it in the database.")
    
    all_orgs = {
        **instance.ORGANIZATIONS['existing_external_orgs'],
        **instance.ORGANIZATIONS['non_existing_external_orgs']
    }
    inverse_orgs = {props.get('Alt Name'): name for name, props in all_orgs.items() if props.get('Alt Name')}
    org_primary_names = list(all_orgs.keys())
    org_alt_names = list(inverse_orgs.keys())
    
    # First, check if the sponsor is an exact match in primary or alternate orgs
    if sponsor in org_primary_names:
        return all_orgs[sponsor]["Primary Code"]
    
    closest_valid_sponsor = find_closest_match(sponsor, org_primary_names, case_sensitive=False)
    if closest_valid_sponsor:
        return all_orgs[closest_valid_sponsor]["Primary Code"]
    
    if sponsor in org_alt_names:
        return all_orgs[inverse_orgs[sponsor]]["Primary Code"]
    
    closest_valid_sponsor = find_closest_match(sponsor, org_alt_names, case_sensitive=False)
    if closest_valid_sponsor:
        return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]
    
    # Extract titles and attempt title-based matching
    titles = extract_titles(sponsor)

    for title in titles:
        if title in org_primary_names:
            return all_orgs[title]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_primary_names, case_sensitive=False)
        if closest_valid_sponsor:
            return all_orgs[closest_valid_sponsor]["Primary Code"]
        
        if title in org_alt_names:
            return all_orgs[inverse_orgs[title]]["Primary Code"]
        
        closest_valid_sponsor = find_closest_match(title, org_alt_names, case_sensitive=False)
        if closest_valid_sponsor:
            return all_orgs[inverse_orgs[closest_valid_sponsor]]["Primary Code"]

    raise Exception(f"Failed to determine a sponsor code for '{sponsor}'")

def determine_activity_type(grant):
    award_type = grant['Award_Type']
    if award_type and award_type in ACTIVITY_ASSOCIATIONS:
        return ACTIVITY_ASSOCIATIONS[award_type]