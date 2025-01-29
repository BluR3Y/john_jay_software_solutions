from classes.MigrationManager import MigrationManager
import warnings
warnings.filterwarnings('ignore')

# Run the program
if __name__ == "__main__":
    # Create a class instance
    # with MigrationManager() as my_instance:
    #     # my_instance.start_migration()
    #     query_grant_ids = my_instance.db_manager.execute_query("SELECT Grant_ID FROM grants")
    #     grant_ids = [grant['Grant_ID'] for grant in query_grant_ids]
    #     grants = []
        
    #     batch_limit = 20
    #     num_grants = len(grant_ids)
    #     last_index = 0
    #     while last_index < num_grants:
    #         new_end = last_index + batch_limit
    #         batch_ids = grant_ids[last_index:new_end]
    #         last_index = new_end
            
    #         # Perform the database query
    #         select_query = f"SELECT * FROM grants WHERE Grant_ID IN ({','.join(['?' for _ in batch_ids])})"
    #         query_res = my_instance.db_manager.execute_query(select_query, batch_ids)
            
    #         # Append the grants to the variable that will store all of them
    #         grants.extend(query_res)
            
    #     my_instance.start_migration(grants)
    with MigrationManager() as my_instance:
        existing_grants = my_instance.feedback_template_manager.df["Proposal - Template"]['proposalLegacyNumber'].tolist()
        
        grants = []
        query_grant_ids = my_instance.db_manager.execute_query("SELECT Grant_ID FROM grants")
        grant_ids = [grant['Grant_ID'] for grant in query_grant_ids if grant["Grant_ID"] not in existing_grants]
        
        for grant_id in grant_ids:
            select_grant_query = my_instance.db_manager.execute_query("SELECT * FROM grants WHERE Grant_ID = ?", grant_id)
            select_total_query = my_instance.db_manager.execute_query("SELECT * FROM total WHERE RFunds_Grant_ID = ?", grant_id)
            select_rifunds_query = my_instance.db_manager.execute_query("SELECT * FROM RIfunds WHERE RIFunds_Grant_ID = ?", grant_id)
            select_pi_query = my_instance.db_manager.execute_query("SELECT * FROM PI_name WHERE PI_Grant_ID = ?", grant_id)
            select_dates_query = my_instance.db_manager.execute_query("SELECT * FROM Dates WHERE Date_GrantID = ?", grant_id)
            select_costshare_query = my_instance.db_manager.execute_query("SELECT * FROM CostShare WHERE GrantID = ?", grant_id)
            select_ffunds_query = my_instance.db_manager.execute_query("SELECT * FROM Ffunds WHERE FFunds_Grant_ID = ?", grant_id)
            select_fifunds_query = my_instance.db_manager.execute_query("SELECT * FROM FIFunds WHERE FIFunds_Grant_ID = ?", grant_id)
            
            grants.append({
                "grant_data": select_grant_query[0],
                "total_data": select_total_query,
                "rifunds_data": select_rifunds_query,
                "pi_data": select_pi_query,
                "dates_data": (select_dates_query[0] if len(select_dates_query) else {}),
                "cost_share_data": select_costshare_query,
                "ffunds_data": select_ffunds_query,
                "fifunds_data": select_fifunds_query
            })

        my_instance.start_migration(grants)