simulation {
    Description="Agent-based fuel cycle simulator"
    InputTmpl="init_template"
    control {
             MinOccurs=1
             Description="Defines simulation time and decay methods"
             MaxOccurs=1
             duration={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the number of timesteps in simulation"
                 ValType=Int
                 }
             startyear={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the year to start the simulation"
                 ValType=Int
                 }
             startmonth={
                 MinOccurs=1
                 MaxOccurs=1
                 Description="the month to start the simulation"
                 ValType=Int
                 ValEnums=[ 1 2 3 4 5 6 7 8 9 10 11 12 ]
                 }
             decay={
                 MinOccurs=0
                 MaxOccurs=1
                 Description="How to model decay in Cyclus"
                 ValType=String
                 ValEnums=["lazy" "manual" "never"]
                 }
             dt={
                 MinOccurs=0
                 MaxOccurs=1
                 ValType=Real
                 Description="duration of a single timestep in seconds"
                 }
             explicit_inventory={
                 MinOccurs=0
                 MaxOccurs=1
                 ValType=Int
                 ValEnums=[0 1]
                 Description="boolean specifying whether or nor to track inventory in each agent"
                 }
             
            }

    archetypes {
        MinOccurs=1
        Description="Defines the archetypes used in this simulation"
        MaxOccurs=1
        spec={
            MinOccurs=1
            lib={MinOccurs=1
                 MaxOccurs=1
                 ValType=String
                }
            name={MinOccurs=1
                 MaxOccurs=1
                 ValType=String
                 }
            }
    }
    
    facility {
        Description="Facility definition block"
        MinOccurs=1
        config = {MinOccurs=1
                  MaxOccurs=1
                  ChildExactlyOne = [KFacility Predator Prey Sink Source Enrichment FuelFab Mixer Reactor Separations Storage]
                  KFacility=
			{InputTmpl="KFacility"
			 current_capacity={MaxOccurs=1 ValType=Real}
			 in_capacity={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 in_commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 k_factor_in={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 k_factor_out={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 max_inv_size={MaxOccurs=1 ValType=Real}
			 out_capacity={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 out_commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 recipe_name={MaxOccurs=1 MinOccurs=1 ValType=String}}
		Predator=
			{InputTmpl="Predator"
			 age={MaxOccurs=1 ValType=Int}
			 birth_and_death={MaxOccurs=1 ValType=Int}
			 commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 consumed={MaxOccurs=1 ValType=Real}
			 dead={MaxOccurs=1 ValType=Int}
			 full={MaxOccurs=1 ValType=Real}
			 hunt_cap={MaxOccurs=1 ValType=Real}
			 hunt_factor={MaxOccurs=1 ValType=Int}
			 hunt_freq={MaxOccurs=1 ValType=Int}
			 lifespan={MaxOccurs=1 ValType=Int}
			 nchildren={MaxOccurs=1 ValType=Real}
			 prey={MaxOccurs=1 MinOccurs=1 ValType=String}
			 success={MaxOccurs=1 ValType=Real}}
		Prey=
			{InputTmpl="Prey"
			 age={MaxOccurs=1 ValType=Int}
			 birth_and_death={MaxOccurs=1 ValType=Int}
			 birth_freq={MaxOccurs=1 ValType=Int}
			 commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 dead={MaxOccurs=1 ValType=Int}
			 nchildren={MaxOccurs=1 ValType=Int}}
		Sink=
			{InputTmpl="Sink"
			 capacity={MaxOccurs=1 ValType=Real}
			 in_commod_prefs={MaxOccurs=1
			                     val={MinOccurs=1 ValType=Real}}
			 in_commods={MaxOccurs=1
			                MinOccurs=1
			                val={MinOccurs=1 ValType=String}}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 max_inv_size={MaxOccurs=1 ValType=Real}
			 recipe_name={MaxOccurs=1 ValType=String}}
		Source=
			{InputTmpl="Source"
			 inventory_size={MaxOccurs=1 ValType=Real}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 outcommod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 outrecipe={MaxOccurs=1 ValType=String}
			 throughput={MaxOccurs=1 ValType=Real}}
		Enrichment=
			{InputTmpl="Enrichment"
			 feed_commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 feed_recipe={MaxOccurs=1 MinOccurs=1 ValType=String}
			 initial_feed={MaxOccurs=1 ValType=Real}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 max_enrich={MaxOccurs=1 ValType=Real}
			 max_feed_inventory={MaxOccurs=1 ValType=Real}
			 order_prefs={MaxOccurs=1 ValType=Int}
			 product_commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 swu_capacity={MaxOccurs=1 ValType=Real}
			 tails_assay={MaxOccurs=1 ValType=Real}
			 tails_commod={MaxOccurs=1 MinOccurs=1 ValType=String}}
		FuelFab=
			{InputTmpl="FuelFab"
			 fill_commod_prefs={MaxOccurs=1
			                       val={MinOccurs=1 ValType=Real}}
			 fill_commods={MaxOccurs=1
			                  MinOccurs=1
			                  val={MinOccurs=1 ValType=String}}
			 fill_recipe={MaxOccurs=1 MinOccurs=1 ValType=String}
			 fill_size={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 fiss_commod_prefs={MaxOccurs=1
			                       val={MinOccurs=1 ValType=Real}}
			 fiss_commods={MaxOccurs=1
			                  MinOccurs=1
			                  val={MinOccurs=1 ValType=String}}
			 fiss_recipe={MaxOccurs=1 ValType=String}
			 fiss_size={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 outcommod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 spectrum={MaxOccurs=1 MinOccurs=1 ValType=String}
			 throughput={MaxOccurs=1 ValType=Real}
			 topup_commod={MaxOccurs=1 ValType=String}
			 topup_pref={MaxOccurs=1 ValType=Real}
			 topup_recipe={MaxOccurs=1 ValType=String}
			 topup_size={MaxOccurs=1 ValType=Real}}
		Mixer=
			{InputTmpl="Mixer"
			 in_streams={MaxOccurs=1
			                MinOccurs=1
			                stream={MinOccurs=1
			                           commodities={MaxOccurs=1
			                                           MinOccurs=1
			                                           item={MinOccurs=1
			                                                    commodity={MaxOccurs=1
			                                                                  MinOccurs=1
			                                                                  ValType=String}
			                                                    pref={MaxOccurs=1
			                                                             MinOccurs=1
			                                                             ValType=Real}}}
			                           info={MaxOccurs=1
			                                    MinOccurs=1
			                                    buf_size={MaxOccurs=1
			                                                 MinOccurs=1
			                                                 ValType=Real}
			                                    mixing_ratio={MaxOccurs=1
			                                                     MinOccurs=1
			                                                     ValType=Real}}}}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 out_buf_size={MaxOccurs=1 ValType=Real}
			 out_commod={MaxOccurs=1 MinOccurs=1 ValType=String}
			 throughput={MaxOccurs=1 ValType=Real}}
		Reactor=
			{InputTmpl="Reactor"
			 assem_size={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 cycle_step={MaxOccurs=1 ValType=Int}
			 cycle_time={MaxOccurs=1 ValType=Int}
			 decom_transmute_all={MaxOccurs=1 ValType=Int}
			 fuel_incommods={MaxOccurs=1
			                    MinOccurs=1
			                    val={MinOccurs=1 ValType=String}}
			 fuel_inrecipes={MaxOccurs=1
			                    MinOccurs=1
			                    val={MinOccurs=1 ValType=String}}
			 fuel_outcommods={MaxOccurs=1
			                     MinOccurs=1
			                     val={MinOccurs=1 ValType=String}}
			 fuel_outrecipes={MaxOccurs=1
			                     MinOccurs=1
			                     val={MinOccurs=1 ValType=String}}
			 fuel_prefs={MaxOccurs=1 val={MinOccurs=1 ValType=Real}}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 n_assem_batch={MaxOccurs=1 MinOccurs=1 ValType=Int}
			 n_assem_core={MaxOccurs=1 ValType=Int}
			 n_assem_fresh={MaxOccurs=1 ValType=Int}
			 n_assem_spent={MaxOccurs=1 ValType=Int}
			 power_cap={MaxOccurs=1 ValType=Real}
			 power_name={MaxOccurs=1 ValType=String}
			 pref_change_commods={MaxOccurs=1
			                         val={MinOccurs=1 ValType=String}}
			 pref_change_times={MaxOccurs=1
			                       val={MinOccurs=1 ValType=Int}}
			 pref_change_values={MaxOccurs=1
			                        val={MinOccurs=1 ValType=Real}}
			 recipe_change_commods={MaxOccurs=1
			                           val={MinOccurs=1 ValType=String}}
			 recipe_change_in={MaxOccurs=1
			                      val={MinOccurs=1 ValType=String}}
			 recipe_change_out={MaxOccurs=1
			                       val={MinOccurs=1 ValType=String}}
			 recipe_change_times={MaxOccurs=1
			                         val={MinOccurs=1 ValType=Int}}
			 refuel_time={MaxOccurs=1 ValType=Int}
			 side_product_quantity={MaxOccurs=1
			                           val={MinOccurs=1 ValType=Real}}
			 side_products={MaxOccurs=1
			                   val={MinOccurs=1 ValType=String}}}
		Separations=
			{InputTmpl="Separations"
			 feed_commod_prefs={MaxOccurs=1
			                       val={MinOccurs=1 ValType=Real}}
			 feed_commods={MaxOccurs=1
			                  MinOccurs=1
			                  val={MinOccurs=1 ValType=String}}
			 feed_recipe={MaxOccurs=1 ValType=String}
			 feedbuf_size={MaxOccurs=1 MinOccurs=1 ValType=Real}
			 latitude={MaxOccurs=1 ValType=Real}
			 leftover_commod={MaxOccurs=1 ValType=String}
			 leftoverbuf_size={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 streams={MaxOccurs=1
			             MinOccurs=1
			             item={MinOccurs=1
			                      commod={MaxOccurs=1
			                                 MinOccurs=1
			                                 ValType=String}
			                      info={MaxOccurs=1
			                               MinOccurs=1
			                               buf_size={MaxOccurs=1
			                                            MinOccurs=1
			                                            ValType=Real}
			                               efficiencies={MaxOccurs=1
			                                                MinOccurs=1
			                                                item={MinOccurs=1
			                                                         comp={MaxOccurs=1
			                                                                  MinOccurs=1
			                                                                  ValType=String}
			                                                         eff={MaxOccurs=1
			                                                                 MinOccurs=1
			                                                                 ValType=Real}}}}}}
			 throughput={MaxOccurs=1 ValType=Real}}
		Storage=
			{InputTmpl="Storage"
			 discrete_handling={MaxOccurs=1 ValType=Int}
			 in_commod_prefs={MaxOccurs=1
			                     val={MinOccurs=1 ValType=Real}}
			 in_commods={MaxOccurs=1
			                MinOccurs=1
			                val={MinOccurs=1 ValType=String}}
			 in_recipe={MaxOccurs=1 ValType=String}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}
			 max_inv_size={MaxOccurs=1 ValType=Real}
			 out_commods={MaxOccurs=1
			                 MinOccurs=1
			                 val={MinOccurs=1 ValType=String}}
			 residence_time={MaxOccurs=1 ValType=Int}
			 throughput={MaxOccurs=1 ValType=Real}}
}
    }
    
    region{
        Description="Region definition block"
        MinOccurs=1
        config= {MinOccurs=1
                 MaxOccurs=1
                 ChildExactlyOne = [NullRegion GrowthRegion]
                 NullRegion=
			{InputTmpl="NullRegion"}
		GrowthRegion=
			{InputTmpl="GrowthRegion"
			 growth={MaxOccurs=1
			            MinOccurs=1
			            item={MinOccurs=1
			                     commod={MaxOccurs=1
			                                MinOccurs=1
			                                ValType=String}
			                     piecewise_function={MaxOccurs=1
			                                            MinOccurs=1
			                                            piece={MinOccurs=1
			                                                      function={MaxOccurs=1
			                                                                   MinOccurs=1
			                                                                   params={MaxOccurs=1
			                                                                              MinOccurs=1
			                                                                              ValType=String}
			                                                                   type={MaxOccurs=1
			                                                                            MinOccurs=1
			                                                                            ValType=String}}
			                                                      start={MaxOccurs=1
			                                                                MinOccurs=1
			                                                                ValType=Int}}}}}
			 latitude={MaxOccurs=1 ValType=Real}
			 longitude={MaxOccurs=1 ValType=Real}}

                 }
        institution={MinOccurs=1
                    config={MinOccurs=1
                            MaxOccurs=1
                            ChildExactlyOne = [NullInst DeployInst ManagerInst]
                             NullInst=
					{InputTmpl="NullInst"}
				DeployInst=
					{InputTmpl="DeployInst"
					 build_times={MaxOccurs=1
					                 MinOccurs=1
					                 val={MinOccurs=1 ValType=Int}}
					 latitude={MaxOccurs=1 ValType=Real}
					 lifetimes={MaxOccurs=1 val={MinOccurs=1 ValType=Int}}
					 longitude={MaxOccurs=1 ValType=Real}
					 n_build={MaxOccurs=1
					             MinOccurs=1
					             val={MinOccurs=1 ValType=Int}}
					 prototypes={MaxOccurs=1
					                MinOccurs=1
					                val={MinOccurs=1 ValType=String}}}
				ManagerInst=
					{InputTmpl="ManagerInst"
					 latitude={MaxOccurs=1 ValType=Real}
					 longitude={MaxOccurs=1 ValType=Real}
					 prototypes={MaxOccurs=1
					                MinOccurs=1
					                val={MinOccurs=1 ValType=String}}}
}
                    initialfacilitiylist={MaxOccurs=1
                                          entry={MinOccurs=1
                                                 number={MaxOccurs=1
                                                         ValType=Int}
                                                 prototype={MaxOccurs=1
                                                            ValType=String}
                                                }
                                         }
                    }
    }
    
    recipe{
        Description="Recipe definition block"
        name={
            MinOccurs=1
            MaxOccurs=1
            ValType=String
            }
        basis={
            MinOccurs=1
            MaxOccurs=1
            ValType=String
            ValEnums=["mass" "atom"]
            }
        nuclide={
            MinOccurs=1
            id={MinOccurs=1 MaxOccurs=1}
            comp={MinOccurs=1 MaxOccurs=1 ValType=Real}
            }
    }

}
