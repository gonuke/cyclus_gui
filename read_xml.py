import xmltodict


def read_xml(path, which):
    with open(path, 'r') as f:
        obj = xmltodict.parse(f.read())

    if which == 'recipe':
        recipe_dict = {}
        n = 0
        xml_list = obj['root']['recipe']
        if not isinstance(xml_list, list):
            xml_list = [xml_list]
        for recipe in xml_list:
            n += 1
            comp_dict = {}
            if not isinstance(recipe['nuclide'], list):
                recipe['nuclide'] = [recipe['nuclide']]
            for entry in recipe['nuclide']:
                comp_dict[entry['id']] = entry['comp']
            recipe_dict[recipe['name']] = {'base': recipe['basis'],
                                           'composition': comp_dict}
        return recipe_dict, n



    if which == 'arche':
        new_arche = []
        n = 0
        xml_dict = obj['archetypes']
        for entry in xml_dict['spec']:
            new_arche.append([entry['lib'], entry['name']])
            n += 1
        return new_arche, n



    if which == 'region':
        n = 0
        region_dict = {}
        xml_list = obj['root']['region']
        if not isinstance(xml_list, list):
            xml_list = [xml_list]

        for region in xml_list:
            region_dict[region['name']] = {}

            if not isinstance(region['institution'], list):
                region['institution'] = [region['institution']]

            for i in region['institution']:
                inst_array = []
                if 'DeployInst' in i['config'].keys():
                    prototypes = i['config']['DeployInst']['prototypes']['val']
                    instname = i['name']

                    if not isinstance(prototypes, list):
                        prototypes = [prototypes]

                    for indx, p in enumerate(prototypes):
                        n += 1
                        entry_list = []
                        entry_dict = i['config']['DeployInst']
                        for cat in ['prototypes', 'n_build', 'build_times', 'lifetimes']:
                            if len(prototypes) == 1:
                                entry_list.append(entry_dict[cat]['val'])
                            else:
                                entry_list.append(entry_dict[cat]['val'][indx])
                        inst_array.append(entry_list)

                if 'initialfacilitylist' in i.keys():
                    init_facility = region['institution']['initialfacilitylist']['entry']
                    if not isinstance(init_facility, list):
                        init_facility = [init_facility]
                    for i in init_facility:
                        n += 1
                        entry_list = [i['prototype'], i['number'], '1', '99999']
                        if 'lifetime' in self.proto_dict[i['prototype']].keys():
                            entry_list[3] = self.proto_dict[i['prototype']]['lifetime']
                        inst_array.append(entry_list)
            region_dict[region['name']][instname] = inst_array

        return region_dict, n


    if which == 'facility':
        
