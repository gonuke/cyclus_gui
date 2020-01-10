simulation{
    Description="Agent-based fuel cycle simulator"
    InputTmpl="init_template"
    control {MinOccurs=1
             MaxOccurs=1
             simhandle={
                 MinOccurs=0
                 MaxOccurs=1
                 ValType=String
             }
             duration={
                 MinOccurs=1
                 MaxOccurs=1
                 ValType=Real
             }
    }
}