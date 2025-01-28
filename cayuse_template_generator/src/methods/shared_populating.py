from datetime import datetime
from methods.utils import find_closest_match

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
        if project_primary_dept in org_units.keys():
            return project_primary_dept, org_units[project_primary_dept]['Primary Code'], None
        else:
            closest_valid_dept = find_closest_match(project_primary_dept, org_units.keys())
            if closest_valid_dept:
                return closest_valid_dept, org_units[closest_valid_dept]['Primary Code'], None
            else:
                if project_primary_dept in org_centers.keys():
                    project_center = org_centers[project_primary_dept]
                    return project_center['Admin Unit'], project_center['Admin Unit Code'], project_primary_dept
                else:
                    closest_valid_center = find_closest_match(project_primary_dept, org_centers.keys())
                    if closest_valid_center:
                        project_center = org_centers[closest_valid_center]
                        return project_center['Admin Unit'], project_center['Admin Unit Code'], closest_valid_center
                    else:
                        raise Exception(f"Failed to determine a valid department for {project_primary_dept}")
    else:
        raise Exception("Grant does not have a primary department in the database.")