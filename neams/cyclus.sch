simulation{
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
        %facility_schema
    }
    
    region{
        Description="Region definition block"
        MinOccurs=1
        %region_schema
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
    doi{}

}
