
simulation{InputType=Sequence InputTmpl='cyclus.seq'
Description="Agent-based fuel cycle simulator"
    control {InputType=Sequence
             MinOccurs=1
             MaxOccurs=1
             simhandle={MinOccurs=0 MaxOccurs=1 ValType=String}
             duration={MinOccurs=1 MaxOccurs=1 ValType=Real}
             } 
}